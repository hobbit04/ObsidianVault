---
tags:
  - 3D
---
복잡한 형상을 단순한 primitive 도형들의 집합 연산으로 조립한다는 3D 모델링 패러다임. 
- Primitives: 구, 큐브, 원기둥 등, 수식으로 정의 가능한 물체
- Operators: 합집합, 차집합, 교집합
- 표현 구조: CSG tree. 잎은 primitive, 내부 노드는 boolean 연산자인 이진 트리
```
        차집합(−)
        /      \
   합집합(∪)    원기둥
    /     \
  육면체    구
```
