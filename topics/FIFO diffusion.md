---
tags:
  - ComputerVision
---
**Title: FIFO-Diffusion: Generating Infinite Videos from Text without Training**
## Introduction
---
기존의 Video Diffusion Models이 긴 동영상 생성에 실패한 이유: 동영상을 3D + 1D(time)으로 해석해 하나의 4D tensor처럼 다루려고 했기 때문. 이러면 scaling이 잘 안됨.

AR 방식을 쓰고 싶은데, 트랜스포머에는 적용이 쉽지만 디퓨전에는 계산량이 많아 적용하기 어려움. 그래서 요즘엔 chunked AR generation 방법을 쓰지만, 자주 temporal inconsistency와 discontinuous motion 문제가 발생함. 
--> 이 문제를 해결하기 위해 FIFO-Diffusion을 제시함

짧은 영상을 생성하는 Pretrained video veneration model을 사용함. 
Chunked AR의 문제를 해결한 방식: 모든 프레임이 충분한 숫자의 이전 프레임들을 참고할 수 있게 함.

\<Queue>
head | ----------------- | tail
Denoised frame     random noise image

장점: 노이즈가 많은 프레임들이 cleaner 한 프레임들을 참고해 디노이징 과정이 잘 일어남
단점: 보통 같은 noise level에서 프레임을 denoise 하는 것을 학습하기 때문에, training-inference gap문제가 심해짐.
--> 이 단점을 극복하기 위해 latent partitioning 을 도입함.

## Text-to-Video Diffusion Models
---
Encoder-Decoder 모델임. noise prediction을 통해 denoise 시킴.
Encoder가 어떤 video $v$를 입력받으면 video latent $z_0$을 만들어 냄. Latent diffusion model이 decoder 역할을 하며, $z_t$를 denoise 하도록 학습됨. 이때 $z_t$는 $z_0$에서 노이즈가 점진적으로 추가된 latent space vector 이며, 각 단계에서 노이즈를 예측하도록 학습됨. 즉 손실 함수는 실제 노이즈와 예측된 노이즈의 차이로 계산됨. 

새로운 영상을 생성할 때는 DDIM 같은 sampler를 이용해 latent를 denoise 시켜 영상을 만듦. 

LDM 논문에서 나온 내용과 유사하지만, text condition $c$가 추가 되었음.

## FIFO-Diffusion
---
### Diagonal denoising
![[Pasted image 20250713154207.png|600]]
점점 노이즈가 많아지는 연속적인 프레임들을 처리한다. 수식으로 표현하면, $$[z_{\tau_0}^1;...z_{\tau_{f-1}}^f]=\Phi([z_{\tau_1}^1;...z_{\tau_f}^f], [\tau_1;...;\tau_f],f; \epsilon_0)$$이다. 이때 $[z_{\tau_1}^1;...z_{\tau_f}^f]$는 대각선으로 나열된 latents로 queue $Q$에 저장되어 있다. 항상 같은 noise를 이용하던 Text-to-video Diffusion models에서의 sampling 수식과 다르다. 이는 아래의 Figure 3 에서도 확인할 수 있다(검정에 가까울 수록 노이즈 많은 프레임).
![[Pasted image 20250713155009.png|600]]
여러개의 프레임들에 대해 동시에 denoising 과정을 수행하지만, output으로는 denoising 과정이 끝난 하나의 frame만 나가게 된다. 
그럼 첫 diagonal latents는 어떻게 설정할까? 이는 $f$ random noises에서 만들어지며 아래 알고리즘을 이용한다. 
![[Pasted image 20250713155807.png|600]]

- 작동 방식: 항상 $f$ 개의 프레임들만 입력으로 받고, sliding window approach를 통해 매 time step마다 1개씩 output frame을 내보냄. 공간 복잡도는 전체 영상 길이에 무관하게 $O(f)$임. 
- 기존의 Chunked AR과 비교;
![[Pasted image 20250713162052.png]]
Chunked 방식의 문제점: condition으로 사용하는 벡터가 이전 프레임들에서 얻은 contextual 정보를 갖고 있지 않아서 여러 chunk간 장기적인 맥락을 유지시키는 것이 힘들다.
FIFO-Diffusion: 국소적인 consistency가 장기적인 sequence로 확장될 수 있게 한다. 또한 별도의 추가학습이나 subnetworks가 필요하지 않다(기존 AR 방식과의 차이점). 

### Latent partitioning
그냥 diagonal denoising만 사용하면 training-inference gap이 생겨 문제가 된다. 이를 해결하기 위한 방법이 latent partitioning. 
1. 큐의 길이를 n배 시킴. 즉 $f\rightarrow nf(n>1)$
2. $n$개의 블록으로 분할시킴. 
3. 각 블록에서 독립적으로 처리.
이렇게 하면 inference steps은 증가하지만, training-inference gap 문제는 해결할 수 있다. 
![[Pasted image 20250713165549.png|600]]
![[Pasted image 20250713170124.png|600]]
$Q$가 $[z_{\tau_1}^1;...;z_{\tau_{nf}}^{nf}]$를 diagonal latents로 갖고 있을 때, 이를 $n$개의 블록으로 나누어 $[Q_0;...;Q_{n-1}]$로 나타내자. 각 블록은 크기가 $f$이고 $Q_k$는 time steps $\tau_k=[\tau_{kf+1};...;\tau_{(k+1)f}]$ 인 latents를 갖고 있다. 각 블록에 대해서 분할정복 방식으로 diagonal denoising을 수행한다. 

장점;
1. Reduces maximum noise level gap between the latents from $|\sigma_{\tau_{nf}}-\sigma_{\tau_1}|$  to $\text{max}_k|\sigma_{\tau_{(k+1)f}}-\sigma_{\tau_{kf+1}}|$. 
2. Improves throughput of inference by parallel operation on GPU.
3. Allow leveraging a large number of inference steps. 

### Lookahead denoising
![[Pasted image 20250713173839.png|600]]
![[Pasted image 20250713174038.png|600]]
Diagonal denoising 과정을 $f$에 대해서 하는게 아니라 $f/2$에 대해서 진행함. 이 프레임들은 더 선명한(denoising 된) 프레임들을 참고해 denoising 된다. 비용이 두 배로 증가하지만, latent partitioning과 마찬가지로 병렬 연산을 통해 해결할 수 있다. 
## Experiment
---
### Implementation details
사용한 Text-to-video DMs: VideoCrafter1, VideoCrafter2, zeroscope, Open-Sora Plan
Sampling 방식: DDIM with $\eta \in \{0.5, 1\}$  
정량평가: FVD$_{128}$, IS scores

### Qualitative results
1. Baseline models이 만들 수 있는 프레임수보다 훨씬 많은 프레임의 동영상을 만들어낼 수 있음. 
2. 각 프레임들도 뛰어난 품질을 갖고 있으며 비디오의 뒷부분까지도 semantic 정보가 유지 됨. 
3. 프롬프트로 물체의 변화를 요구해도 잘 반영 됨. (e.g., c = "호랑이가 걷다가 가만히 선 후 앉는다")
4. Training-free 방식의 모델, chunked AR 방식의 모델들과 비교해도 움직임의 부드러움이나 프레임 퀄리티, scene의 다양성 측면에서 outperform 함.

### Quantitative results
![[Pasted image 20250713221223.png|600]]PVDM-L과의 비교: 얘는 long video generation을 위해 만들어진 모델이지만, diffusion steps를 400번이나 하는데도 불구하고 64번의 steps을 이용하는 FIFO diffusion 모델보다 좋은 성능을 보였다.

## Computational cost
Memory usage와 inference time per frame을 구했음. 
![[Pasted image 20250713221521.png|600]]


## Limitations and Questions
---
1. 왜 추론 단계에서 노이즈 레벨이 학습 단계에서의 레벨과 크게 달라 training-inference gap 문제가 심해지는 것인지 이유를 잘 모르겠음
2. 아무리 병렬 연산이 가능하다고는 하지만, 여전히 여러 GPU를 활용해야 하기 때문에 높은 비용이 필요함. 
3. 설문조사의 과정이 어떻게 되었는지 나와 있지 않음. 
4. 결국 training-inference gap을 완전히 해결하지는 못했다고 인정함. 