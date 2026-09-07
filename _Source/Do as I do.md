---
title: |-
  Do as I Do: Dexterous Manipulation Data
  from Everyday Human Videos
School:
  - UCBerkeley
tags:
  - 3D
  - Robotics
---
[[Do as I do.pdf]]
## Task
로봇을 학습 시키기 위한 데이터를 만드는 것이 목표다. 구체적으로, 인터넷에서 가져온 평범한 monocular 동영상을 dexterous hand 로봇이 실행할 수 있는 데이터로 바꾸는 것이 목표다. 
## Previous Limits
- 손과 물체의 4d 상태를 monocular video에서 가져오기가 쉽지 않았음
- 사람의 손과 로봇의 손의 근본적인 구조적 차이 때문에 naive한 retargeting이 잘 통하지 않음
## Methods
크게 *reconstruct* $\rightarrow$ *retarget* 의 두 단계 pipeline으로 이루어져있다.
![[Pasted image 20260906123617.png]]
### Reconstruction
Vision foundation model을 이용해 아무 비디오에서 사람의 손과 물체를 인식한다. 
- Hand tracking: HawoR 사용 + 세가지 전처리 적용
	- segmentation(SAM3)
	- depth + camera intrinsics(MoGe)
	- object mesh 생성(SAM 3D)
- Object tracking: SAM 3D 기반의 모델 제작해서 사용

### Retargeting
Hand-object 데이터를 robot hand로 바꾸는 단계다.
기존에 이 단계를 다룬 연구들은 완전하지 못해서, 저자들은 *Dynamics aware retargeting*이라는 방법을 제시한다. 이 방법에는 세 가지 기법이 적용된다.
![[Pasted image 20260906130104.png]]
1. **Warmup steps.** 초반 프레임들은 plan window가 움직일 때 매우 적은 횟수만 해당된다. 초반이라 노이즈도 많은데 planning을 많이 거치지도 못함. 이런 문제를 해결하기 위해 초반에 $H$개의 스텝을 추가하는 것을 warmup steps라고 한다. 이때는 물체를 강제로 고정시키고 손만 움직일 수 있도록 한다(세 가지 개선안들 중 가장 큰 성능 향상 기여).
2. **Random force perturbation.** 물체를 불안하게 잡고 있을 때, 이는 local minima로 이해할 수 있다. 물체가 타겟을 따라가긴 하는데, 안정적이진 않다. 이런 행동의 기댓값을 떨어트려 안정적인 동작을 만들기 위해 랜덤하게 외력을 가한다. 외력을 가해도 안정적으로 물체를 잡고 동작을 이어나가게 만들기 위함이다.
3. **Transition reward.** 물체의 상태는 rest, 또는 in-hand 가 될 수 있다. 이 상태가 원본과 맞지 않는 매 timestep마다 negative reward를 줘서 물체를 잡아야 할 때 잡고, 놓아야 할 때 놓을 수 있게 학습시킨다. 
