---
tags:
  - 3D
  - ComputerVision
---
Paper: [[Ben Mildenhall 2020]]

Neural Radiance Fields의 약자로, Novel View Synthesis를 해결하기 위해 MLP를 사용하는 방법이다. 3D model reconstruction을 해결하려는 것이 아니다. 크게 *Scene을 표현하는 방법* 과 *렌더링 방법* 두 단계에서 설명이 필요하다.
## Scene의 표현 방법
$$F_\Theta:(x,d)\rightarrow (c, \sigma)$$위의 수식이 NeRF의 표현 방법이다. $\Theta$로 파라미터화 된 신경망 $F_\Theta$는 두 개의 입력을 받는다. $x, d$는 각각 카메라의 위치와 시점(각도)을 의미한다. ![[Pasted image 20260818220103.png]]
위 figure를 보면 두 번째 사진에 카메라의 다양한 위치와 각도들이 표시된 것을 볼 수 있다. 이 정보를 받아, 모델은 $c, \sigma$를 내놓는다. 이는 각각 radiance(빛)와 volume density이다. 
### 다른 방법들과의 차이점
[[Signed Distance Function]], [[Occupancy Function]] 등의 방법에서는 표면이 정의 되고, 각 위치에서 표면과의 관계(가까운지, 혹은 안쪽인지 등)를 output으로 내놓았다. 그래서 색을 입히려면 별도의 텍스쳐와 조명 모델이 필요했는데, NeRF의 모델은 $c$ 까지 output 해 자체적으로 색을 표현할 수 있다. 

위에서 살짝 언급했듯이, NeRF에서는 표면이 정의 되지 않는다. 자세한 사항은 아래의 *렌더링 방법* 부분에서 설명하겠다. 아무튼 이렇게 volume으로 문제를 해결하기 때문에 안개나 머리카락처럼 경계를 정의하기 어려운 scene을 표현하는데 유리하고, watertight 해야 한다는 전제가 필요 없어진다는 장점이 생긴다. 반면 표면이 어딘지가 중요한 task에서는 NeRF를 활용하기 어려울 것이다. 

마지막으로, NeRF는 