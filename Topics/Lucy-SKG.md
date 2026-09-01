---
tags:
  - ReinforcementLearning
---
## Introduction 
---
History: 
> Element(첫 Deep RL bot) -> Necto(2022 RL Bot Championship winner) -> Nexto(Successor of Necto) -> Lucy-SKG(Based on Necto)

Necto와 Nexto를 상대로 연전연승을 거둘 뿐만 아니라 학습 시간도 줄일 수 있었다.
(SKG stands for, **Shaping Kinesthetic IntelliGence**)

Main contributions
1. Reward analysis 및 시각화 라이브러리 개발
2. KRC의 제안 및 사용
3. 이전 행동들을 포함하는 것이 state space에 얼마나 정보 손실을 일으키며 어떤 효과를 가지는지 연구
4. 학습가능한 새로운 보상 함수를 만들어 비슷한 게임들에 적용할 수 있음

## Related Work
---
**Necto vs Nexto**
1. an action space with explicit rules that prohibit certain invalid action combinations that remove learning load and substitute it with explicit human knowledge
2. a tweaked version of Necto’s reward function
3. more network parameters

## Background
---
### Reward Shaping
여러 MDP와 마찬가지로, RocketLeague도 보상이 너무 sparse 하다는 문제가 있다. 이는 $R'$을 보상으로 하는 새로운 MDP, $M'$을 만들어 해결할 수 있다. $$M'=(S,A,p,\gamma, R')$$
- $S$: state space
- $A$: action space
- $p$: environment dynamic function(how does the env change)
- $\gamma$: discount factor for reward
- $R'=R+F$ where $F(s,a,s')=\gamma\Phi(s')-\Phi(s)$ : shaped reward function
여기서 $\Phi$는 현재 state의 quality를 측정하는 potential 함수다.

게임이 너무 복잡하기 때문에, $R$과 $F$ 모두 여러 보상 함수들의 선형 조합으로 구성했다. 
$\Phi$는 $m$개의 $\Phi_i$로 나눠지고, 이를 각각 general utility와 utilities 라고 한다. 각 $\Phi_i$는 다시 state utilities 와 player utilities로 나눠진다.

### Auxiliary Tasks
