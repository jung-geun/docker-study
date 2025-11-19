# 건국대학교 차세대 분산시스템 강의 자료

이 저장소는 건국대학교에서 2025년 2학기 차세대 분산시스템 수업을 위해 만들어졌습니다.
Docker와 Kubernetes를 학습하기 위한 실습 자료와 예제 코드를 포함하고 있습니다.

## 📚 강의 목차

### [02. Docker 기본](./02-docker-basics/README.md)

- Docker 기본 개념과 실습
- Docker 설치 및 기본 명령어
- 이미지와 컨테이너 관리
- Dockerfile 작성법

### [03. Docker Compose](./03-docker-compose/README.md)

- Docker Compose를 활용한 멀티 컨테이너 관리
- docker-compose.yml 파일 작성
- 서비스 간 네트워킹
- 볼륨과 환경 변수 관리

### [04. Kubernetes 기본](./04-k8s/README.md)

- Kubernetes 기본 개념과 아키텍처
- K3s를 이용한 경량 쿠버네티스 설치
- kubectl 명령어 사용법
- 간단한 애플리케이션 배포 및 관리

### [05. ReplicaSet과 Deployment](./05-replicaset_and_deployment/README.md)

- ReplicaSet과 Deployment의 개념
- 레플리카셋과 디플로이먼트 실습
- 서비스(Service) 개념과 실습
- 로드밸런싱과 서비스 디스커버리

### [06. Volume, ConfigMap, Secret](./06-volume_configmap_secret/README.md)

- ConfigMap을 이용한 설정 관리
- Volume을 이용한 데이터 영속화
- Secret을 이용한 민감 정보 관리

### [07. DaemonSet과 모니터링](./07-daemonset/README.md)

- DaemonSet의 개념과 활용
- Node Exporter를 이용한 노드 메트릭 수집
- Prometheus와 Grafana를 이용한 모니터링 시스템 구축

### [08. Ingress](./08-ingress/README.md)

- Ingress의 개념과 활용
- 간단한 파일 서버 애플리케이션 배포
- Ingress 리소스를 이용한 외부 접근 제어

### [09. Helm으로 패키징하기](./09-helm/README.md)

- Helm 차트를 이용한 쿠버네티스 애플리케이션 패키징
- Values와 템플릿을 활용한 재사용 가능한 매니페스트 관리
- 다양한 환경에 대한 배포 전략
- Ingress 실습을 Helm 차트로 변환

## 🚀 시작하기

각 강의별 디렉토리로 이동하여 해당 README.md 파일을 참조하세요.

## 요구사항

- Docker Desktop 또는 Docker Engine 설치
- 기본적인 터미널/CLI 사용 지식

## 📞 문의

강의나 실습 관련 문의사항이 있으시면 언제든지 연락주세요.

mail: [pieroot@konkuk.ac.kr](mailto:pieroot@konkuk.ac.kr)
