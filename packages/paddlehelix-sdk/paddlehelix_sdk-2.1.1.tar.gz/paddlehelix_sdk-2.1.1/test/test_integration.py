import time
import multiprocessing
import pytest
from paddlehelix.task import common
from paddlehelix.task import helixfold3
from test.test_task.test_helixfold3 import find_all_test_cases

@pytest.mark.stress
def test_stress_all():
    cases = find_all_test_cases('ligand_posebuster')[:1] * 500
    processes = []
    for i in range(0, 6):
        process = multiprocessing.Process(target=helixfold3.execute, args=(f'stress_all/{i}', cases, True, True))
        process.start()
        processes.append(process)

    # 实测并发6进程，每分钟可以提交约 250 条任务，这里等待 10 分钟，可以提交 2500 条任务
    time.sleep(10 * 60)
    for process in processes:
        process.terminate()
        process.join()

    fs = []
    canceled_num = 0
    with multiprocessing.Pool(6) as pool:
        for i in range(0, 6):
            fs.append(pool.apply_async(common.cancel, args=(f'stress_all/{i}', None, True)))

        for f in fs:
            canceled_task_ids = f.get()
            canceled_num += len(canceled_task_ids)
        assert canceled_num > 1500, "压测过程中取消任务的数量显著低于预期！共提交2500条任务，实际取消数量为{}".format(canceled_num)
