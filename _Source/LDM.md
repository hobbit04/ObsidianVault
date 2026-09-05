**Title: High-Resolution Image Synthesis with Latent Diffusion Models**

*Topics to study more*
- Autoencoder: 입력을 latentspace의 벡터로 축소 시키는 한편 해당 벡터를 다시 원본 입력으로 만드는 과정을 통해 encoder는 특징들을 잘 추출해내게 되고, decoder는 추출된 특징으로부터 원본에 가까운 결과를 만들어낼 수 있게 된다. 대표적인 비지도학습 방식.
- VAE: Variational AutoEncoder의 약자로, 
- Latent space: Encoder가 생성한 feature vector가 존재하는 벡터 공간
- Cross attention
- Auto regressive transformer
- Stroke-based synthesis: 이미지를 픽셀 단위로 만드는 것이 아니라 stroke를 기본 단위로 사용해 stroke 단위로 이미지를 생성하는 방식. pixel-based 방법과 대조된다. 
- Mode-collapse
- training instabilities
- GANs
- UNet backbone
- Token-based conditioning mechanisms
- VQ-VAEs, VQGANs
- KL-reg
- DDIM
## Idea of the paper
---
이미지 생성은 너무 비싼 작업이다. 특히 고화질의 복잡한 자연 풍경 같은 것들. 
이미지 생성 학습을 처음부터 하는 대신 auto encoder가 만들어 놓은 latent space에서부터 diffusion을 수행하면 복잡도는 줄이면서 특징들은 유지할 수 있다.
Cross attention을 통해 conditioning도 가능하다. 

기본적으로 DM(diffusion models)은 likelihood-based models 이다.

Pixel space에서 학습된 DM을 이용한다. 

적은 step만으로도 고해상도 이미지를 생성해낼 수 있다.

score-based model과 같이 학습하는 방법도 존재했지만, 이 방법이 더 높은 성능을 보였다.

## Method
---
*기호 정리*
- $x$: image
- $\varepsilon$: encoder. $x$ -> latent representation
- $z$: $\varepsilon$에 $x$를 넣어 얻은 결과
- $\mathcal{D}$: decoder
- $\tilde{x}$: decoder의 결과로 생성된 이미지
- $p(x)$: image $x$에 대한 확률 분포($x$가 나올 확률분포)
- $y$: Condition. Can be text, image, etc,.
- $\tau_{\theta}$: Domain specific encoder. $\tau_{\theta}(y) \in \mathbb{R}^{M \times d_\tau}$ 

인코더가 이미지를 다운 샘플링 할 때는 가로 세로의 축소 비율이 $f$로 같다. 논문에선 이를 $2^m$으로 설정.

Diffusion Models를 UNet backbone에 cross attention mechanism을 적용한 모델로 확대해 conditioning이 가능하도록 했다.
![[Pasted image 20250628133439.png]]

## Experiments
---
$f$의 적절한 값은 4 or 8.
