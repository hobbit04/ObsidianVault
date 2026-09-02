---
title: Structured 3D Latents for Scalable and Versatile 3D Generation
citekey: xiang2025trellis
venue: CVPR
school:
  - Tsinghua University
  - USTC
lab:
  - Microsoft Research
tags:
  - paper
---
[[TRELLIS.pdf]]

## Task
고품질의 3D asset을 만들어내는 새로운 방식의 3D 생성 기법을 제안한다. 

## Previous Limits
- **3D 생성 모델.** 직접 3d representations 를 생성하는 것을 학습하는, 어찌보면 가장 직관적인 접근. 하지만 3d 데이터는 근본적으로 sparse 하기 때문에, 효율성을 높이는 것이 문제가 된다. 
- **2D 생성 모델로 3D 만들기.** 2D 생성 모델은 어쩔 수 없이 multiview inconsistent 하다. 이를 기반으로 만드니 해당 한계를 그대로 물려받는다.
- **Rectified flow models.** 요건 좀 좋다. 그래서 이 논문에서도 이 기법을 scale 하는 방법을 제시한다. 

## Method
3D representation의 종류에 관계 없이 고품질의 3D assets을 만들어내기 위해, [[Structured Latent]]를 제시한다. 

## Numbers
## Conclusion