import multiprocessing as mp
import time
import pandas as pd


# dataframe = pd.DataFrame(data)


def do_something(listOfNumbers):
    sum = 0
    for i in listOfNumbers:
        sum += i
    time.sleep(1)


if __name__ == "__main__":
    listOfNumbers = [1, 2, 3, 4, 5]
    start = time.time()

    processes = []

    for _ in range(10):
        p = mp.Process(target=do_something, args=(listOfNumbers))
        p.start()
        processes.append(p)

    for process in processes:
        process.join()

    end = time.time()
    print(f"Finished script in: {end-start} sec")
