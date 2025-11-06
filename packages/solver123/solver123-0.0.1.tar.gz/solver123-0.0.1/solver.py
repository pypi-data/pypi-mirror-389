# solver.py
import subprocess
import re

def main():
    # 1) /flag 바이너리 실행 (실제 경로에 맞게 수정 가능)
    p = subprocess.Popen(
        ["/flag"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )

    # 2) 첫 줄(문제) 읽기: "1234 * 5678 + 910 = ?"
    line = p.stdout.readline()

    # 3) 숫자 세 개 뽑아서 계산
    nums = list(map(int, re.findall(r"\d+", line)))
    A, B, C = nums
    ans = A * B + C

    # 4) 정답 보내기
    p.stdin.write(str(ans) + "\n")
    p.stdin.flush()

    # 5) 나머지 출력 읽기 (여기에 플래그가 있을 것)
    print(p.stdout.read())

if __name__ == "__main__":
    main()
