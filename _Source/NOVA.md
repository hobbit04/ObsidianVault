---
tags:
  - ComputerVision
---
**Title: AUTOREGRESSIVE VIDEO GENERATION WITHOUT VECTOR QUANTIZATION**

*Key Idea: Video를 생성하는 autoregressive model을 vector quantization 없이 가능케 했다*

## Introduction
---
기존 방식의 문제점
- Vector quantization: VQ tokenizers가 높은 표현력과 압축성을 동시에 갖기 힘들었다.
- Diffusion: 대부분의 모델이 고정 길이 프레임들의 joint distribution만 학습해서 다양한 길이에서의 비디오 생성 능력을 갖기 힘들었다. 또 AR 모델의 in-context 능력을 갖지 못했다.
NOVA: 비디오 생성모델에서 quantization을 사용하지 않고 AR model을 사용한 첫 사례이다.
시간 순서대로, 한 프레임 내에서는 random order로 토큰 생성한다.

Video generation 문제를 frame-by-frame prediction + set-by-set prediction 으로 분리해 해결한다. 

MAR이랑 똑같은거 아니냐! -> 전혀 사소하지 않은 차이가 존재..
1. NOVA는 효율성, scalability, mask schedule 문제를 해결. Class-to-image 대신 text-to-image에서 이를 해결함. 
2. 먼저 temporal frames를 예측하고(casual order) 각 프레임의 set들을 예측하는(random order) 방식으로 작동. 
## Related works
---
- Diffusion model
- Raster-scan AR model: 이미지를 픽셀 또는 패치 단위로 왼쪽위에서 오른쪽 아래 순서로 예측하는 방식
- MAR
- Emu3
위의 두 AR 방법은 AR video generation approaches의 두 종류이다.
## Methodology
---
### Rethinking AR models for video generation
AR video generation에는 두 가지 방식이 있다.
1. Token-by-token generation via raster scan order
> Sausal per-token 예측을 통해 동영상 프레임 시퀀스를 생성하고, token들을 순서대로(raster scan ordering) 디코딩 한다.

2. Masked set-by-set generation in a random order
> 비디오 프레임의 모든 토큰을 동등하게 취급해 양방향 트랜스포머 디코더를 사용한다. 

이 둘을 조합한 것이 NOVA
### Temporal AR modeling via Frame-by-frame prediction
Pre-trained language model을 사용해 text prompts -> features 을 수행한다. 이 논문은 텍스트와 비디오를 입력 받아 새로운 비디오의 생성을 목적으로 하고 있다. 
- OpenCV를 이용해 optical flow 측정. Average flow magnitude를 일종의 motion score로 사용한다. 
- VAE로 temporal 처리
- 추가적인 임베딩 레이어를 이용해 latent video와 트랜스포머의 채널을 정렬

비디오 프레임은 causal sequence로 볼 수 있기 때문에 block-wise causal masking attention을 사용해 각 프레임이 텍스트 프롬프트, video flow, 그리고 이전 프레임들에 영향을 받도록 한다. 
![[Pasted image 20250707091828.png|500]]
한 프레임 내의 각 토큰은 서로 참조할 수 있지만, 서로 다른 프레임들은 조건(text prompts, video flow)과 이전 프레임들만 참조할 수 있다. 이를 수식으로 표현하면 다음과 같다;$$p(P, m, B, S_1,...,S_F)=\prod_f^Fp(S_f|P,m,B,S_1,...,S_f-1)$$여기서 $P, m$은 각각 텍스트 프롬프트와 video flow를 나타낸다. $S_f$는 $f$번째 프레임의 모든 토큰들을 나타내는 집합이다. $B$는 BOV(begin of video) 임베딩을 나타낸다. 즉 첫 비디오 프레임을 예측하는 학습가능한 벡터다. 우변의 $p(\cdot)$을 적절히 바꾸면 text-to-image, image-to-video 문제를 표현하는 모델로 바꿀 수 있다. 학습 효율도 증가되고 kv-cache를 이용할 수도 있게 하는 장점이 있다. 

AR 모델은 transformer로 구성되는데, 이는 기본적으로 토큰의 순서에 대한 정보를 갖고 있지 않다. 그래서 positional embedding이 필요한데, 시간은 1차원, 공간은 2차원 임베딩이 필요하다. 이를 위해서 sine-cosine embeddings를 각각 1-D, 2-D 버전으로 사용했다. ![[Pasted image 20250710021617.png]]
즉 이 figure의 아래, Temporal Layers에는 1-D positional embedding이 사용되고 위의 Spatial Layers에는 2-D positional embedding이 사용되는 것이다. 
### Spatial AR modeling via Set-by-set prediction
![[Pasted image 20250710022734.png]]
먼저 (a)를 보면, 왼쪽의 그림은 Temporal per-token을 나타낸다. 이는 NOVA 모델에서 사용하는 방식이 아니며, 비교를 위해 나타낸 것이다. 가로 방향으로 토큰을 생성하며, 이때 참조(attend)할 수 있는 토큰을 색칠한 것이다. 오른쪽 그림, 즉 Temporal per-frame을 보면 각 프레임 하나를 만들 때 참조할 수 있는 토큰의 종류는 현재 프레임의 모든 토큰과 이전 프레임의 토큰, 그리고 prompt 및 video flow 이다. 

시도했던 실험: Temporal layers의 output을 spatial layer에서 단순히 Condition이 아닌 indicator features로 사용하면 어떨까?
결과: image structure의 붕괴 및 균일하지 못한 video fluency
원인 분석: 이웃한 프레임들 사이의 indicator features는 비슷해서, 모델이 정확한 연속적인 motion change를 학습하는 것이 어려워짐. Ground truth의 정보를 indicator feature로 줬을 때도 weak robustness and stability로 이어짐.
-> Scaling and Shift layer 도입
결국 indicator feature를 사용하긴 해야 하는데(?), 위의 두 방식은 실패함. 대신 BOV vector를 기준(anchor)으로 해서 변형을 가함. 현재 프레임의 평균과 분산 역할을 하는 값을 MLP를 통과 시켜 구함. 이후 normalize 과정을 거쳐 $S_f'$을 indicator features로 사용함. 첫 프레임에 대해서는 $\gamma=1, \beta=0$으로 설정함. 
![[Pasted image 20250710033906.png|300]]
### Diffusion procedure denoising for Per-token prediction
학습시 Diffusion loss를 사용해 per-token probability를 예측한다. 
추론시 denoise 과정을 이용해 노이즈로부터 프레임을 생성한다. 이는 MAR에서 사용하는 방식과 동일한 것으로 보인다. 
## Experiment
---
### Setup

### Main results
![[Pasted image 20250710034436.png]]
먼저 Text-to-image task를 평가하면 위와 같다. GenEval, T2I-CompBench, DPG-Bench 등에서 sota 또는 경쟁력 있는 성능을 보였다. 대부분의 specialized text-to-image 모델들보다 좋은 성능이 나온다. 

![[Pasted image 20250707151036.png]]
더 적은 수의 파라미터로 비슷하거나 더 좋은 성능을 보였다. 특히, AR model들보다는 압도적으로 좋았고 Diffusion 모델들과도 비슷비슷한 성능을 보였다. 

## Conclusion
---
Text-to-image는 매우 좋은 성능을 보였고, video 생성에도 괜찮은 성능을 보였다.

## Limitations and Questions
---
1. 33 frames 만 만들 수 있도록 설계 되었는데, 동영상 길이를 늘리기 위해 pre-filling 방법을 사용함. 그럼 애초에 더 긴 동영상을 생성하도록 설계된 모델과 성능이 다를텐데, 실험에서 생성한 동영상은 몇 프레임짜리 동영상인지 언급해야 하는 것 아닌가?
2. 동영상 프레임들이 시간 순서대로 연속적일 것이란 가정하에 causal attention을 사용하지만, 실제 동영상은 편집 등으로 인해 불연속적인 전환이 있을 수 있다. 이런 데이터에 대해서는 성능이 떨어질 듯.
3. 