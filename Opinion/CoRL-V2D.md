## Setup
현재 `wonguyn_sim`에 접속해서 `~/` 에 git clone 해놓은 상태. 
쿠버네틱스 접속 파일은 `~/.kube/`에 있음. 
서버 접속 테스트를 위해 repo의 `/rlwrld/k8s/README.md` 의 내용 실행 중. 구체적으로, 
```
cp rlwrld/.env.example rlwrld/.env
# in rlwrld/.env:
#   V2D_USER=<you>                       # names your jobs <you>-* and your EFS folder
#   V2D_KUBECONFIG=<path of your kubeconfig>
#   V2D_EFS_ROOT=/data/<you>/<project>   # your working folder on the shared EFS
kubectl --kubeconfig <path> auth can-i create jobs     # yes
rlwrld/k8s/render.py smoke --apply --deadline 3600 --ttl 3600
kubectl --kubeconfig <path> logs -f job/<you>-v2d-smoke   # last line: SMOKE_ALL_OK 17/17
```
의 마지막 줄 실행 결과 기다리는 중. -> 완료
```
wongyun@sim:~/CoRL-V2D$ kubectl logs -f job/sungjae-v2d-smoke
NVIDIA L40S, 46068 MiB, 580.178.04, 8.9
OK   shim:anycalib  [smoke] env=/opt/envs/anycalib torch=2.7.1+cu128 cuda_build=12.8 gpu=True torch_from=/opt/conda/lib/python3.11/site-pack
OK   shim:moge  [smoke] env=/opt/envs/moge torch=2.7.1+cu128 
...(중략)
SMOKE_ALL_OK 17/17
```

- [x] 질문: kubeconfig의 내용을 서버에서 개인 컴퓨터로 받아와서 작업해도 되는지? 즉 `wongyun_sim`의 `~/.kube/`아래의 내용을 다운 받아도 괜찮은지.
- [x] 질문: 현재 `rlwrld/.env`의 내용을 `sungjae`로 해놓았는데, 선배님도 `wongyun_sim`에서 작업하시는지? 즉 `.env`의 내용을 바꿔야할지
## Current state analysis
1. ![[Pasted image 20261008150002.png]]아무리 worst case라지만 어떻게 이런 오류가 발생할 수 있지? 그리고 ep23, ep24에 