import concurrent.futures
import multiprocessing as mp
import time


def do_something(seconds, listOfNumbers):
    print(f"Sleeping {seconds} second(s)...")
    # time.sleep(seconds)
    sum = 0
    for i in listOfNumbers:
        sum += i
    return f"Done Sleeping... and sum: {sum}"


if __name__ == "__main__":
    start = time.time()

    my_list = [i for i in range(1, 1000001)]

    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = [
            executor.submit(do_something, 1, my_list) for _ in range(10)
        ]  # list comprehension

    # sequential version -------------------
    # results = []
    # for _ in range(10):
    #     results.append(do_something(1, my_list))

    print("Results: ")
    for f in concurrent.futures.as_completed(results):
        print(f.result())

    # sequential version -------------------
    # for r in results:
    #     print(r)

    end = time.time()
    print(f"Finished script in: {end-start} sec")
    coresAmount = mp.cpu_count()
    print(f"Amount of cores: {coresAmount}")
