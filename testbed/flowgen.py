import argparse
import heapq
import random
import socket
import threading
import time

ANDAZE_BAR = 22
TEDADE_BASTE = 6
FASELE_BASTE = 0.25


def _goosh(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", port))
    while True:
        try:
            s.recvfrom(2048)
        except OSError:
            return


def harif(args):
    soketha = []
    for _ in range(args.n):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("0.0.0.0", 0))
        soketha.append(s)
    bar = b"\0" * ANDAZE_BAR
    shoroo = time.time()
    for t in range(args.dur):
        for s in soketha:
            s.sendto(bar, (args.dst, args.port))
        time.sleep(max(0.0, shoroo + t + 1 - time.time()))
    for s in soketha:
        s.close()


def hame_be_hame(args):
    threading.Thread(target=_goosh, args=(args.port,), daemon=True).start()
    rng = random.Random(args.seed)
    digaran = [h for h in (int(x) for x in args.hosts.split(",")) if h != args.me]
    bar = b"\0" * ANDAZE_BAR
    shoroo = time.time()
    saf = []
    for i in range(args.n):
        maghsad = "10.0.0.%d" % (rng.choice(digaran) + 1)
        heapq.heappush(saf, (shoroo + i * args.dur / args.n, i, maghsad, None, TEDADE_BASTE))
    while saf:
        zaman, i, maghsad, s, mande = heapq.heappop(saf)
        time.sleep(max(0.0, zaman - time.time()))
        if s is None:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind(("0.0.0.0", 0))
        s.sendto(bar, (maghsad, args.port))
        if mande > 1:
            heapq.heappush(saf, (zaman + FASELE_BASTE, i, maghsad, s, mande - 1))
        else:
            s.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["adv", "alltoall"], required=True)
    ap.add_argument("--dst")
    ap.add_argument("--me", type=int)
    ap.add_argument("--hosts")
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--dur", type=int, required=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    if args.mode == "adv":
        harif(args)
    else:
        hame_be_hame(args)


if __name__ == "__main__":
    main()
