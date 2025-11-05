import sys
import threading
from multiprocessing.managers import BaseManager
import time
from queue import Queue

queues = {
    # 检测队列
    'detect0': Queue(),
    'detect1': Queue(),
    'detect2': Queue(),
    'detect3': Queue(),
    'detect4': Queue(),
    'detect5': Queue(),
    'detect6': Queue(),
    'detect7': Queue(),
    'detect8': Queue(),
    'detect9': Queue(),
    'detect10': Queue(),
    'detect11': Queue(),
    'detect12': Queue(),
    'detect13': Queue(),
    'detect14': Queue(),
    'detect15': Queue(),
    'detect16': Queue(),
    'detect17': Queue(),
    'detect18': Queue(),
    'detect19': Queue(),
    'detect20': Queue(),
    # 结果队列
    'ret0': Queue(),
    'ret1': Queue(),
    'ret2': Queue(),
    'ret3': Queue(),
    'ret4': Queue(),
    'ret5': Queue(),
    'ret6': Queue(),
    'ret7': Queue(),
    'ret8': Queue(),
    'ret9': Queue(),
    'ret10': Queue(),
    'ret11': Queue(),
    'ret12': Queue(),
    'ret13': Queue(),
    'ret14': Queue(),
    'ret15': Queue(),
    'ret16': Queue(),
    'ret17': Queue(),
    'ret18': Queue(),
    'ret19': Queue(),
    'ret20': Queue(),
    # 显示 队列
    'show0': Queue(),
    'show1': Queue(),
    'show2': Queue(),
    'show3': Queue(),
    'show4': Queue(),
    'show5': Queue(),
    'show6': Queue(),
    'show7': Queue(),
    'show8': Queue(),
    'show9': Queue(),
    'show10': Queue(),
    'show11': Queue(),
    'show12': Queue(),
    'show13': Queue(),
    'show14': Queue(),
    'show15': Queue(),
    'show16': Queue(),
    'show17': Queue(),
    'show18': Queue(),
    'show19': Queue(),
    'show20': Queue(),
    # 采集 队列
    'capture0': Queue(),
    'capture1': Queue(),
    'capture2': Queue(),
    'capture3': Queue(),
    'capture4': Queue(),
    'capture5': Queue(),
    'capture6': Queue(),
    'capture7': Queue(),
    'capture8': Queue(),
    'capture9': Queue(),
    'capture10': Queue(),
    'capture11': Queue(),
    'capture12': Queue(),
    'capture13': Queue(),
    'capture14': Queue(),
    'capture15': Queue(),
    'capture16': Queue(),
    'capture17': Queue(),
    'capture18': Queue(),
    'capture19': Queue(),
    'capture20': Queue(),
}


class QueueManager(BaseManager):
    pass


class WinQueueFounder:
    def __init__(self, ip_addr='127.0.0.1', Port=9001, authkey='gotion'):

        self.server_addr = ip_addr
        self.port = Port
        self.authkey = bytes(authkey, 'utf-8')
        self.nq = 0
        self.que_name = []

    def init_server(self, **kwargs):
        self.startServer(**kwargs)

    def startServer(self, **kwargs):
        for k, v in kwargs.items():
            for i in range(int(v)):
                name = str(k) + str(i)
                QueueManager.register(name, callable=lambda n=name: queues[n])
                self.nq += 1
                self.que_name.append(str(k) + str(i))
        print('queue number:', self.nq)
        print('queue name:', self.que_name)
        manager = QueueManager(address=(self.server_addr, self.port),
                               authkey=self.authkey)  # 口令必须写成类似b'abc'形式，只写'abc'运行错误
        s = manager.get_server()
        print('queue server init done')
        monitor_thread = threading.Thread(target=self.monitor_queue_size)
        monitor_thread.setDaemon(True)
        monitor_thread.start()
        s.serve_forever()

    def connectQue(self, camId, name='ret'):
        '''
        连接queue
        '''
        connected = False
        while connected == False:
            try:
                QueueManager.register('%s%s' % (name, camId))
                manager = QueueManager(address=(self.server_addr, self.port), authkey=self.authkey)
                manager.connect()
                det_sender = eval('manager.%s%s()' % (name, camId))
                connected = True
                print('queue %s%s connect success' % (name, camId))
                return det_sender
            except Exception as e:
                print('%s%s_Connect error:' % (name, camId), str(e))
                time.sleep(1)

    def monitor_queue_size(self):
        while True:
            # 监听队列是否超过20个元素
            for one_queue_name in self.que_name:
                if queues[one_queue_name].qsize() > 20:
                    print(one_queue_name, '大于', 20, '开始删除')
                    while queues[one_queue_name].qsize() > 20:
                        queues[one_queue_name].get()
            time.sleep(5)  # 每秒检查一次


if __name__ == '__main__':
    # TEST
    if sys.platform.lower() == 'win32':
        from multiprocessing import freeze_support

        freeze_support()
        qf = WinQueueFounder()
        qf.init_server()
    else:
        pass
