---
tags:
  - 3D
  - ComputerVision
---
Paper: [[Bernhard Kerbl 2023]]
Demo: https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/

줄여서 3DGS 라고도 하는 이 기법은, 3D scene을 약 수백만 개의 수많은 3D 가우시안들의 합으로 기술하는 방법이다. 신경망을 사용하지 않는, explicit 한 3d representation 방법이다. 
## Scene 표현 방법
3DGS에서 하나의 3D scene은 약 $10^6$개의 가우시안으로 표현된다.

하나의 가우시안은, 다음과 같은 파라미터를 가진다.

| 파라미터                                | 의미                              |
| ----------------------------------- | ------------------------------- |
| $\mu \in \mathbb{R}^3$              | 중심 위치                           |
| $\Sigma \in \mathbb{R}^{3\times 3}$ | 모양/방향 cf) [[Covariance Matrix]] |
| $\alpha$                            | 불투명도                            |
| SH 계수                               | View-dependent 색상               |
위 네 개의 파라미터로 정의되는 가우시안 $G(x)$는 다음과 같다. $$G(x)=\exp(-\frac{1}{2}(x-\mu)^T\Sigma^{-1}(x-\mu))$$우선 주목할 점은 가우시안 분포에는 존재하는 정규화 상수가 위 식에는 없다는 것이다. $G$는 단지 가우시안 모양만 기술하고, 확률 밀도 함수로 볼 수 없다. 

### $\mu$, 중심위치
말 그대로 3차원 상의 위치를 의미한다. 그럼 어떤 위치에 물체가 있는지 어떻게 알고 해당 위치를 특정할 수 있을까? 일단 점을 찍어야, 그 주변에 가우시안 분포를 그리든 할 수 있을테니 말이다. 

논문에선 [[Johannes L. Schonberger 2016]]의 COLMAP을 활용한다. COLMAP은 결과물로 카메라 pose와 sparse [[Point Cloud]]를 출력한다. 이때 하나의 point가 하나의 가우시안으로 대응되는 것이다. COLMAP 덕분에 3DGS는 사진들만을 이용해 결과물을 만들 수 있다(pose도 loss 정의를 위해 필요함). 
### $\Sigma$
3차원 가우시안의 모양을 살펴보자.
![[Pasted image 20260822231556.png]]
(출처: https://xoft.tistory.com/49)
1차원에서는 분산 $s^2$ 하나만으로 가우시안의 모양(위치 제외)을 결정할 수 있었지만, 3차원에선 공분산 행렬이 필요하다. [[Covariance Matrix]]에서 $\Sigma=V\Lambda V^T$로 고윳값 분해를 한 결과를 해석한 바 있다. 여기선 $\Sigma=V\Lambda V^T=RSS^TR^T=RS^2R^T$로 나타내고 의미를 해석해보자(이렇게 두는 이유는 아래에 서술). 먼저 $R$은 $V$와 동일한 행렬로 둘 수 있으므로 eigen vector, 다시말해 타원체의 세 주축의 방향을 의미하는 행렬이 될 것이다. 그리고 $S^2$은 $\Sigma$의 eigen value를 대각원소로 갖는 대각 행렬이 된다. 대응되는 eigen vector 축으로 퍼진 정도를 의미한다.

우리는 [[Covariance Matrix]]를 학습시킬 것이고, 이 행렬은 PSD를 만족해야 하기 때문에, 6개의 자유도를 주는 것 외에도 추가로 제한을 둬야 한다. 그 제한은 $\Sigma = RSS^TR^T$로 두는 것이다. 이렇게 두면 $A=RS$라 할 때 $\Sigma=AA^T$로 둘 수 있고, $$x^T\Sigma x=x^TAA^Tx=||A^Tx||^2\geq 0, \ \forall x$$이므로 항상 PSD한 행렬로 만들 수 있다. 

$A=RS$로 두는 것에 대해 직관적인 해석도 가능하다. 단위 구를 변형시킨 것이 3D Gaussian이라고 할 수 있는데, 단위 구를 축 방향으로 늘리는(Scale) 행렬이 $S$, 회전(Rotation) 시키는 행렬이 $R$, 그리고 특정 위치로 옮겨 놓는 과정은 $\mu$를 더하는 것으로 이해할 수 있다.

$R$과 $S$는 행렬 형태로 저장되는 대신, 각각 q와 s라는 벡터로 저장되고 계산된다. 순서를 바꿔 먼저 $S$부터 살펴보자.
$S=\text{diag}(e^{s_x}, e^{s_y}, e^{s_z})$ 로 저장된다. $s=(s_x,s_y,s_z)$에서 $s$의 자유도는 3임을 볼 수 있다. $s$에 저장되는 값은 표준편차이고 타원체의 형태를 나타내게 된다.
$q$라고 하는 값은 회전 쿼터니언으로, 네 개의 자유도를 갖는 벡터다. $R$이 회전벡터가 되려면 $R^TR=I$ 조건이 성립해야 하는데, 그냥 9개의 자유도를 가진 행렬 $R$을 학습시키면 gradient decent 과정에서 이 조건이 무너진다. 따라서 쿼터니언을 사용해 R을 나타내고, 크기가 1이 되도록 정규화(이때 자유도 하나 감소)를 시켜 사용하면 6개의 자유도를 갖도록 맞출 수 있다. 
(쿼터니언에 대한 추가 학습 필요...) 
### $\alpha$
[[NeRF]]에서도 나왔던 $\alpha$는 $\sigma$를 통해 간접적으로 얻는 대신 직접 구하는 방법을 택한다. 0과 1 사이의 값이 나와야 하기 때문에 sigmoid를 거쳐 사용한다. $\sigma$와 마찬가지로 view와 상관없는 값이다. 

### SH계수
SH 계수는 [[Spherical Harmonics]]의 설명을 참고하자.

## Rendering 방법
[[NeRF]] 같은 신경망 forward 과정이 없어 매우 빠르게 렌더링을 할 수 있다. 전체적인 렌더링 과정은 다음과 같다.
1. Culling
2. Projection
3. Binning
4. Blending
### Projection
[[EWA Volume Splatting]]을 이용한다.
### Binning


## 학습 방법