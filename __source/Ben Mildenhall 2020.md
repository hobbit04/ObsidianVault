---
Conference: ECCV
School:
  - UC Berkeley
  - UC San Diego
Lab:
  - Google Research
Title: "NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis"
---
[[NeRF.pdf]]

(아래 정리된 내용은 2025년에 공부했던 내용을 그대로 가져온 것)
## Introduction
성과: 복잡한 scene에 대한 새로운 시각을 합성해 내는 방식의 발전을 이룸
Input: 위치 + 보는 각도 (3+2차원)
Output: volume density(밀도 $\sigma$)와 radiance(빛 $c$)
(주의: $\sigma$는 불투명도가 아니라 미분 확률밀도이다. 불투명도 $\alpha_i = 1-\exp(-\sigma_i\delta_i)$는 여기서 유도되는 값이다.)
![[Pasted image 20260818220103.png]]
*Task를 설명하는 사진*

Convolutional layers를 전혀 사용하지 않고 MLP 만을 이용해 개발함
대략적인 방법
1. 카메라 광선(ray)을 장면 안으로 march시켜 광선 위의 3d points를 샘플링한다
2. 샘플된 3d point $x$와 그에 대응하는 2d viewing direction $d$를 입력으로 하여 색상과 밀도를 출력하는 신경망을 설계 (신경망의 입력은 카메라의 위치가 아니라 광선 위의 샘플 점이라는 점에 주의)
3. 전통적인 volume rendering 방법을 이용해 output된 정보들로 2d image를 만들어낸다. 
![[Pasted image 20260818220118.png]]
cf) [[Voxel]], [[Signed Distance Function]]

Contributions:
1. 간단한 MLP로 연속적이고 복잡한 구조의 물체를 표현하는 방법을 제시함
2. 렌더링 과정을 미분가능한 방법으로 수행하는 방법을 제시함
3. 5D 입력을 고차원에 대응시키는 positional encoding의 도입으로 high-frequency scene도 최적화 할 수 있었음
## Neural Radiance Field Scene Representation
연속적인 scene을 함수로 나타낸다. 
location + viewing direction -> color & volume density
MLP로 위의 함수를 나타냈다. 
$F_\Theta : (x,d)\rightarrow (c,\sigma)$ 
,where 
- $x$: 3d location
- $d$: 3d Cartesian unit vector(개념상으로는 2개의 자유도를 갖지만 신경망이 표현하기 쉽도록 3차원 단위 벡터를 사용한 것)
- $c$: color = (r, g, b)
- $\sigma$: density
이때, $\sigma$는 오직 $x$에 대해서만 예측되도록 한다. 반면 $c$는 $x$와 $d$ 모두에 대해서 예측되도록 한다. 
이를 구현하기 위해 먼저 $x$만을 입력으로 하는 8층의 fully-connected layers를 이용한다. 이 신경망은 output으로 $\sigma$와 256차원의 feature vector를 내놓게 되는데, 이 feature vector에다가 또 다른 input인 $d$를 concat 하여 추가적인 하나의 fully-connected layer를 통과시킨다. 이 신경망은 $c$를 내놓게 되고, 이는 $x, d$ 모두에 대해 영향을 받은 output이다. 
- 이렇게 하는 이유는? -> Multiview consistent 하도록 하기 위해서

## Volume Rendering with Radiance Fields
신경망이 내놓은 색상($c$)과 밀도($\sigma$) 정보를 이용해 최종적으로 픽셀 하나의 값을 만들어내는 방법을 설명하고 있다. 
이미지들을 이용해 일종의 3D 모델링(Radiance field 생성)을 MLP가 해놓았으니, 우리가 원하는 시점(카메라의 위치, 방향)에서 해당 3D 객체가 어떻게 '보일지' 계산을 하는 과정이 필요하다. 이는 전통적인 volume rendering 과정을 통해 수행된다.
ray를 나타내는 수식: $r(t)=o +td$ 
$o$: 카메라의 위치
$t$: 카메라에서 ray 방향으로 떨어진 거리
$d$: 카메라가 바라보는 방향(unit vector). 위치가 아님에 주의 
$$C(r)=\int_{t_n}^{t_f}T(t)\sigma(r(t))c(r(t), d)dt$$
, where $T(t) = \text{exp}(-\int_{t_n}^t \sigma(r(s))ds)$. <- accumulated transmittance along the ray from $t_n$ to $t$.
위의 수식은 연속적인 공간에서 수행하는 이상적인 계산이고, 실제로는 N개의 샘플을 구하고 이들에 대한 summation을 하는 식으로 구한다.
$$\hat{C}(r)=\sum_{i=1}^NT_i(1-\text{exp}(-\sigma_i\delta_i))c_i$$
, where $T_i=\text{exp}(-\sum_{j=1}^{i-1}\sigma_j\delta_j)$

- $\delta_i$: 인접한 샘플과의 거리, 즉 $t_{i+1}-t_i$. 

미분 가능한 식이기 때문에 gradient descent를 사용할 수 있다.

## Optimizing a Neural Radiance Field
위의 방식들만으로 sota 수준의 scene을 만들어내는 것은 불가능했다. 따라서 두 가지 방법을 추가로 도입해 개선을 이뤄냈다. 
### Positional encoding
$F_\Theta$ network의 입력으로 $xyz\theta\phi$를 직접 넣는 것은 색상과 형태에 high-frequency variation이 있는 경우 안 좋은 성능을 보였다. 따라서 $F_\Theta$를 두 개로 쪼갠다. 
$F_\Theta=F_\Theta'\circ \gamma$ 
이때 $\gamma$가 positional encoding 역할을 하고, 1차원을 2L 차원으로 변환하는 함수다. Transformer 구조에 사용되는 positional encoding과 형태는 유사하지만 동일하지는 않다. 주파수 스케줄이 다르고(Transformer: $1/10000^{2i/d}$, NeRF: $2^0 \sim 2^{L-1}$), 목적도 다르다. Transformer는 토큰의 *순서*를 주입하려는 목적이고, NeRF는 네트워크가 표현할 수 있는 *주파수 대역폭을 넓히려는* 목적이다.
### Hierarchical volume sampling
렌더링의 효율성을 높이는 것이 이 방식의 목표이다. 이를 위해 coarse와 fine 두 개의 네트워크를 두고, 물체가 있을 법한 중요한 영역에 **샘플을 더 몰아주는** 방식을 사용한다.
- 주의: 공간을 나눠 영역별로 다른 네트워크를 골라 쓰는 것이 아니다. **두 네트워크 모두 광선 전 구간을 담당**하며, 차이는 어느 영역을 맡느냐가 아니라 샘플을 어디에 배분하느냐(sample allocation)에 있다.
- coarse: stratified 샘플 $N_c$개($=64$)로 광선 전체를 훑는다.
- fine: coarse가 만든 분포로 $N_f$개($=128$)를 추가 샘플링한 뒤, $N_c+N_f$개 **전부**에 대해 평가한다. 
1. $N_c$개의 위치에 대해서 $\hat{C}_c(r)=\sum_{i=1}^{N_c}w_ic_i$을 계산한다. (이때 $w_i=T_i(1-\text{exp}(-\sigma_i\delta_i))$)
2. $w_i$들을 이용해 $\hat{w}_i=\frac{w_i}{\sum_{j=1}^{N_c}w_j}$를 만들고, ray를 따라 나타낸 일종의 확률밀도함수로 사용한다.
3. 위 확률밀도함수로부터 inverse transform sampling을 이용해 $N_f$개의 위치를 추가로 샘플링하고, fine 네트워크는 첫번째와 두번째 샘플 set을 **합친 전체**에 대해 평가한다. 
4. 최종적으로 $N_c+N_f$개의 샘플을 이용해서 ray $\hat{C}_f(r)$을 계산한다. 
## Results

- 렌더링 방식으로 합성된 물체, 실제 물체에 대해서 모두 학습을 해봤음
- Neural Volumes, Scene Representation Networks, and Local Light Field Fusion 의 방법들과 비교를 진행했음.
