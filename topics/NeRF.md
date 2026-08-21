---
tags:
  - 3D
  - ComputerVision
---
Paper: [[Ben Mildenhall 2020]]

Neural Radiance Fields의 약자로, Novel View Synthesis를 해결하기 위해 MLP를 사용하는 방법이다. 3D model reconstruction을 해결하려는 것이 아니다. 크게 *Scene을 표현하는 방법* 과 *렌더링 방법* 두 단계에서 설명이 필요하다.
## Scene의 표현 방법
$$F_\Theta:(x,d)\rightarrow (c, \sigma)$$위의 수식이 NeRF의 표현 방법이다. $\Theta$로 파라미터화 된 신경망 $F_\Theta$는 두 개의 입력을 받는다. $x$는 **광선 위에서 샘플링된 3D 점**이고, $d$는 **그 광선의 방향**이다. $x$를 카메라의 위치로 오해하기 쉬운데 그렇지 않다. ![[Pasted image 20260818220103.png]]
위 figure를 보면 두 번째 사진에 카메라의 다양한 위치와 각도들이 표시된 것을 볼 수 있다. 이 정보를 받아, 모델은 $c, \sigma$를 내놓는다. 이는 각각 radiance(빛)와 [[Volume Density]]이다.
이 모델의 구조는 아래와 같다.
![[Pasted image 20260821195519.png]]
특이사항은 $\sigma$를 출력할 때는 $d$를 전혀 관여시키지 않는다는 것이다. 이는 Multiview Consistency를 만족시키기 위한 디자인으로, volume density가 카메라가 보는 각도에 따라 달라지면 안되기 때문이다. 하지만 색은 각도에 따라 달라질 수도 있으므로 $d$를 포함시켜 계산한다. 
## Rendering 방법



### 다른 방법들과의 차이점
[[Signed Distance Function]], [[Occupancy Function]] 등의 방법에서는 표면이 정의 되고, 각 위치에서 표면과의 관계(가까운지, 혹은 안쪽인지 등)를 output으로 내놓았다. 그래서 색을 입히려면 별도의 텍스쳐와 조명 모델이 필요했는데, NeRF의 모델은 $c$ 까지 output 해 자체적으로 색을 표현할 수 있다. 

위에서 살짝 언급했듯이, NeRF에서는 표면이 정의 되지 않는다. 자세한 사항은 아래의 *렌더링 방법* 부분에서 설명하겠다. 아무튼 이렇게 volume으로 문제를 해결하기 때문에 안개나 머리카락처럼 경계를 정의하기 어려운 scene을 표현하는데 유리하고, watertight 해야 한다는 전제가 필요 없어진다는 장점이 생긴다. 반면 표면이 어딘지가 중요한 task에서는 NeRF를 활용하기 어려울 것이다. 

마지막으로, NeRF는 3D 형상에 대한 ground truth가 필요하지 않다. 여러 시점에서 촬영된 2D 이미지와 그에 대응하는 카메라 포즈만 있으면 학습이 된다. 다만 "2D만 쓴다"고 말하면 과장인데, 카메라 포즈는 보통 COLMAP 같은 [[Structure from Motion]]으로 추정하기 때문이다. 정확히는 *형상에 대한 GT는 필요 없지만 카메라 기하는 주어져야 한다*가 맞다. 이 전제마저 없애려는 시도가 BARF, NeRF-- 같은 pose-free 후속 연구들이다.

이때 시점이 **여러 개**여야 한다는 점이 중요하다. 시점이 하나뿐이면 그 사진을 그대로 외워버리는 해가 무수히 많아 형상이 결정되지 않는다. 즉 3D 구조는 직접 감독된 적이 없고, 여러 시점의 사진을 하나의 장면 표현으로 동시에 설명해야 한다는 제약의 부산물로 창발한다. 이를 가능하게 하는 것이 미분 가능한 volume rendering이며, 픽셀 오차의 gradient가 렌더링 식을 거슬러 올라가 광선 위 샘플들의 $(c,\sigma)$로 전파된다.

[[Jeong Joon Park 2019|DeepSDF]]와 대비되는 지점이 여기다. DeepSDF는 $(x, f(x))$ 샘플 쌍이 있어야 하고, 그 GT를 만들려면 watertight [[Mesh]]와 부호 판정이 선행되어야 한다. 3D 정답이 있어야 3D 표현을 배우는 구조인 것이다.

단, 2D 감독 자체를 NeRF가 처음 해낸 것은 아니라는 점은 짚어둘 필요가 있다. Scene Representation Networks나 Neural Volumes 등이 이미 이미지만으로 학습하고 있었고, 논문에서도 이들을 비교 대상으로 삼는다. NeRF의 기여는 2D 감독이라는 패러다임의 발명이 아니라, 연속적인 radiance field와 volume rendering, positional encoding의 조합으로 품질을 도약시킨 데 있다.
