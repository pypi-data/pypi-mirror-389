# -*- coding:utf-8 -*-
import asyncio
import aioredis
from random import randint
import json
import time
from typing import Any, Dict
from appPublic.worker import get_event_loop, schedule_interval, schedule_once
from appPublic.uniqueID import getID
from appPublic.log import debug, exception

class LongTasks:
	def __init__(self, redis_url, taskname, worker_cnt=2, stuck_seconds=600, max_age_hours=3):
		self.redis_url = redis_url
		self.worker_cnt = worker_cnt
		self.taskname = taskname
		self.max_age_seconds = max_age_hours * 3600
		self.task_queue = f'{taskname}_pending'
		self.processing_queue = f'{taskname}_processing'
		self.stuck_seconds = stuck_seconds
		self.redis = None
	
	async def repush_pending_task(self):
		async for key in self.redis.scan_iter(match=f"{self.taskname}:task:*"):
			task = await self.redis.hgetall(key)
			if task['status'] == 'PENDING':
				jstr = json.dumps({
					"task_id": task['task_id'],
					"payload": json.loads(task['payload'])
				})
				await self.redis.rpush(self.task_queue, jstr)
				debug(f'{jstr=}, {self.task_queue=}')
		
	async def cleanup_expired_tasks(self):
		"""清理超过 max_age_hours 的任务"""
		now = time.time()
		debug('cleanup_expired_tasks() called ...')
		async for key in self.redis.scan_iter(match=f"{self.taskname}:task:*"):
			taskid = key.split(':')[-1]
			task = await self.redis.hgetall(key)
			if not task:
				debug(f'{key} task not found')
				await self.redis.delete(key)
				await self.redis.lrem(self.task_queue, 0, key)  # 从任务队列中移除（可选）
				continue

			created_at = task.get("created_at")
			if not created_at:
				await self.redis.delete(key)
				await self.redis.lrem(self.task_queue, 0, key)  # 从任务队列中移除（可选）
				await self.delete_redis_task(taskid)
				debug(f'{key}, {task} no created_at key')
				continue

			created_at = float(created_at)
			if created_at + self.max_age_seconds < now:
				debug(f"🧹 删除过期任务: {key}, {task}")
				await self.redis.delete(key)
				await self.redis.lrem(self.task_queue, 0, key)  # 从任务队列中移除（可选）
			status = task.get('status')
			if status not in ['SUCCEEDED', 'FAILED', 'RUNNING', 'PENDING']:
				debug(f"🧹 删除任务: {key}, {task}")
				await self.redis.delete(key)
				await self.redis.lrem(self.task_queue, 0, key)  # 从任务队列中移除（可选）

	async def process_task(self, payload:dict, workid:int=None):
		sec = randint(0,5)
		await asyncio.sleep(sec)
		debug(f'{payload=} done')
		return {
			'result': 'OK'
		}

	async def start_redis(self):
		self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)

	async def run(self):
		await self.start_redis()
		await self.cleanup_expired_tasks()
		schedule_interval(3600, self.cleanup_expired_tasks)
		schedule_interval(300, self.recover_stuck_tasks)
		workers = [asyncio.create_task(self.worker_loop(i)) for i in range(self.worker_cnt)]
		try:
			await asyncio.gather(*workers)
		except asyncio.CancelledError:
			for w in workers:
				w.cancel()
		finally:
			await self.redis.close()

	async def update_task_hash(self, task_id: str, mapping: Dict[str, Any]):
		# all values must be str
		# str_map = {k: json.dumps(v) if not isinstance(v, str) else v for k, v in mapping.items()}
		await self.set_redis_task(task_id, mapping)
	
	async def recover_stuck_tasks(self):
		"""
		启动时或定期调用，检查 processing_queue 中可能卡住的任务，
		如果某任务的 task:{id}.started_at 距现在 > self.stuck_seconds，则认为卡住并重新入队或标记为 failed。
		"""
		# 读取整个 processing_queue（注意：当队列非常大时需改成分页）
		debug('recover_stuck_tasks() called')
		items = await self.redis.lrange(self.processing_queue, 0, -1)
		now = time.time()
		for task_id in items:
			info = await self.get_redis_task(task_id)
			if not info:
				# 如果 task hash 不存在，可选择直接删除或重新 enqueue
				# 这里我们选择重新入队并删除 processing entry
				await self.redis.rpush(self.task_queue, task_id)
				await self.redis.lrem(self.processing_queue, 1, task_id)
				debug(f"[recover] requeued missing-hash {task_id}")
				continue

			started_at = float(info.get("started_at") or 0)
			status = info.get("status")
			if status == "RUNNING" and (now - started_at) > self.stuck_seconds:
				# 任务卡住 -> 重新入队并更新 attempts 或直接标记失败
				# 示例：重新入队并增加 attempts 字段
				attempts = int(json.loads(info.get("attempts") or "0"))
				attempts += 1
				await self.update_task_hash(task_id, {"status": "PENDING", "attempts": attempts})
				await self.redis.rpush(self.task_queue, task_id)
				await self.redis.lrem(self.processing_queue, 1, task_id)
				debug(f"[recover] task {task_id} requeued due to stuck")
			# else: 正常 running 或其他状态，不处理

	async def worker_loop(self, worker_id: int):
		debug(f"[worker {worker_id}] start")
		while True:
			try:
				# BRPOPLPUSH: 从 task_queue 弹出（阻塞），并 push 到 processing_queue（原子）
				# aioredis: brpoplpush(source, destination, timeout)
				# debug(f"Before BRPOPLPUSH: {self.task_queue} length = {await self.redis.llen(self.task_queue)}")
				task_id = await self.redis.brpoplpush(self.task_queue, self.processing_queue, timeout=5)
				if not task_id:
					await asyncio.sleep(0.1)
					# debug(f'No task in task queue {self.task_queue=}, {self.processing_queue=}')
					# await self.repush_pending_task()
					continue
				else:
					debug(f'get task_id={task_id}')

				task_obj = await self.get_redis_task(task_id)
				payload = task_obj["payload"]

				# 1) 更新 task hash 为 running（这一步很重要：客户端读取到状态）
				started_at = time.time()
				await self.update_task_hash(task_id, {
					"status": "RUNNING",
					"started_at": started_at,
					# optional: increment attempts
				})

				# 2) 执行任务（catch exceptions）
				try:
					result = await self.process_task(worker_id, payload)
				except asyncio.CancelledError:
					# 若希望支持取消，可把 status 设为 cancelling 等
					await self.update_task_hash(task_id, {"status": "FAILED", "error": "cancelled"})
					# 移除 processing_queue 项（已处理）
					await self.redis.lrem(self.processing_queue, 1, task_id)
					continue
				except Exception as e:
					# 写回失败信息
					await self.update_task_hash(task_id, {
						"status": "FAILED",
						"error": str(e),
						"finished_at": time.time()
					})
					# 从 processing_queue 移除该项
					await self.redis.lrem(self.processing_queue, 1, task_id)
					continue

				# 3) 写回成功结果并移除 processing_queue 项
				await self.update_task_hash(task_id, {
					"status": "SUCCEEDED",
					"result": result,
					"finished_at": time.time()
				})
				# 最后一步：从 processing_queue 中移除任务项（LREM）
				await self.redis.lrem(self.processing_queue, 1, task_id)
				debug(f"[worker {worker_id}] finished {task_id}")

			except asyncio.CancelledError:
				break
			except Exception as e:
				exception(f"[worker {worker_id}] loop error: {e}")
				await asyncio.sleep(1)

	async def submit_task(self, payload):
		taskid = getID()
		task_data = {
			"task_id": taskid,
			"status": "PENDING",
			"created_at": time.time(),
			"payload": json.dumps(payload)
		}
		await self.set_redis_task(taskid, task_data)
		await self.redis.rpush(self.task_queue, taskid)
		return {'task_id': taskid}
	
	async def all_taks_status(self):
		x = False
		async for key in self.redis.scan_iter(match=f"{self.taskname}:task:*"):
			taskid = key.split(':')[-1]
			task = await self.get_redis_task(taskid)
			print(f'{task}')
			x = True
		return x

	async def set_redis_task(self, taskid, task_data):
		str_map = {k: json.dumps(v) if not isinstance(v, str) else v for k, v in task_data.items()}
		await self.redis.hset(f"{self.taskname}:task:{taskid}", mapping=str_map)

	async def get_redis_task(self, taskid):
		task = await self.redis.hgetall(f'{self.taskname}:task:{taskid}')
		return task

	async def delete_redis_task(self, taskid):
		await self.redis.delete(f'{self.taskname}:task:{taskid}')

	async def get_status(self, taskid:str):
		task = await self.get_redis_task(taskid)
		if not task:
			return {'error': 'no task'}
		return task

if __name__ == '__main__':
	async def main(lt):
		for i in range(0, 10):
			payload = {
				"task": f"task {i}"
			}
			x = await lt.submit_task(payload)
		while True:
			x = await lt.all_taks_status()
			if not x:
				break
			print('\n')
			await asyncio.sleep(10)

	lt = LongTasks('redis://127.0.0.1:6379', 'test')
	loop = get_event_loop()
	loop.create_task(lt.run())
	loop.run_until_complete(main(lt))
