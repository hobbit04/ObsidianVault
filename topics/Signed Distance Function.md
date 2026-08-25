---
tags:
  - 3D
  - ComputerVision
---
[[Occupancy Function]]와 비슷한 관계에 있는 implicit 표현 방법 중 하나로, 아래와 같이 정의된다.
## 정의
$$f(x)=
\begin{cases}
-d(x,\partial \Omega) & x\in \Omega\\[4pt]
+d(x, \partial \Omega) & x\notin \Omega
\end{cases}$$
여기서 $\Omega$는 어떤 닫힌 표면의 내부를 의미하는 집합이다. 이때 닫힌 표면은 $\partial \Omega$로 나타낼 수 있는데 $\partial$은 위상수학 등에서 경계 연산자를 의미한다. 즉, $\partial$ 기호가 집합 앞에 붙으면 해당 집합의 경계를 의미한다. 

$d(x, \partial \Omega)$는 위치 $x$에서 표면까지의 최단 거리를 의미하고, 부호는 물체 내부 점인 경우 음수(-), 외부 점인 경우 양수(+)로 결정된다. 

그 이유는 이렇게 해야 SDF의 gradient 방향이 surface 바깥을 향하기 때문이다. 게다가 거리 함수이기 때문에 gradient의 크기도 모든 위치에서 1이다([[Eikonal equation]]). 두 결과가 합쳐지면 표면에서 SDF의 gradient가 곧 표면의 [[Normal]]이라는 결론을 얻을 수 있다. 

## 성질
- 연속 공간에서 미분 가능. [[Voxel]]의 이산화 한계를 극복한다. 
- [[Mesh]]와 달리 연결성을 관리할 필요가 없다. 
- [[Constructive Solid Geometry|CSG]] 연산이 매우 가볍게 정의됨

마지막 성질에 대해 자세히 풀어보자면, $f_A,\ f_B$를 각각 물체 $A,\ B$의 SDF라고 할 때 세 가지 불린 연산은 아래와 같이 나타낼 수 있다.

$$
\begin{aligned}
f_{A\cup B}(x) &= \min\big(f_A(x),\ f_B(x)\big) && \text{(union)} \\[6pt]
f_{A\cap B}(x) &= \max\big(f_A(x),\ f_B(x)\big) && \text{(intersection)} \\[6pt]
f_{A\setminus B}(x) &= \max\big(f_A(x),\ -f_B(x)\big) && \text{(difference)}
\end{aligned}
$$

즉 [[Mesh]]에서라면 교선 계산과 재삼각화가 필요한 연산이, SDF에서는 함수값의 $\min/\max$ 한 번으로 끝난다. 

## 표면 추출 / 렌더링
- [[Marching Cubes]]
- Sphere Tracing

## GT 생성
현실적으로 모든 위치에서의 SDF를 구하는 것은 불가능하고, 샘플 쌍의 집합으로 저장된다. 따라서 어디를 샘플링 할지와 그 위치에서의 값을 어떻게 계산할지 라는 두 개의 문제를 풀어야 한다. 보통 [[Mesh]]를 이용해 GT를 생성한다(Depth map과 TSDF fusion으로 근사하는 방법도 있는 것 같은데, GT라고 볼 수는 없는 것 같음).

1. Watertight 하도록 전처리
2. 모든 Query $x$에 대해 모든 face까지의 최단거리 중 최솟값을 구함
3. 부호를 판정하기 위해 Ray stabbing, [[Normal]]이용, Generalized Winding Number 등의 기법 활용

Query를 잘 고르기 위한 방법으로는 [[Jeong Joon Park 2019|DeepSDF]] 에서 제안한 방법이 관행이다. 
- 표면에서 균일 샘플 후 **가우시안 노이즈로 perturb** (보통  두 스케일 혼합) — 약 95%
- 나머지는 **unit sphere 내 uniform** — 전역 구조 학습용
- 이유: 정보량이 표면 근처에 집중되어 있고, 먼 영역은 값이 뻔하기 때문

## 한계
1. 닫힌(watertight) 형상을 전제로 하기 때문에 열린 표면은 부호를 정의할 수 없다.
2. Ground Truth를 생성할 때 non-watertight [[Mesh]]의 경우 전처리를 해야 한다.
3. 신경망이 학습한 $f_\theta$는 [[Eikonal equation|Eikonal]] 조건을 근사적으로만 만족하기 때문에 정규화 손실이 필수적이다.