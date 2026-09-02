---
title: "Lift4D: Harmonizing Single-View 3D Estimation for 4D Reconstruction In-the-Wild"
venue: CVPR
school:
  - Carnegie Mellon University
tags:
  - paper
---
[[Lift4D.pdf]]

## Task
하나의 시점에서 촬영된 In-the-wild video를 이용해 4D Reconstruction을 수행하는 것을 목표로 한다. 

## Previous Limits
크게 두 가지 접근 방식과 한계가 있다.
1. **직접 4D 표현을 예측하는 방식.** 이 방식은 4D training data가 너무 희소하다는 문제에 부딛힌다. 한마디로 데이터셋이 잘 구축되어 있지 않다.
2. **최적화 기반 방식.** 3D 데이터를 최대한 이용하는 방식으로 이를 우회하지만, 시간 정보가 없기 때문에 정적인 priors와 동적인 sequences를 잇는 것에서 어려움을 겪는다
## Method
Data-driven priors를 활용해 4D reconstruction을 하는 것이 핵심이다.
## Numbers
## Conclusion
