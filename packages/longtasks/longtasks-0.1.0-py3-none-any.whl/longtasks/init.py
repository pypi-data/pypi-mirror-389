from ahserver.serverenv import ServerEnv
from longtasks.longtasks import Longtasks
from appPublic.worker import schedule_once

class MyTasks(LongTasks):
	async def process_task(self, payload):
		....

def load_longtasks()
	longtasks = MyTasks('redis://127.0.0.1:6379', 'example')
	env = ServerEnv()
	env.longtasks = longtasks
	schedule_once(0.1, longtasks.run)

