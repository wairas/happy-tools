# happy-tools 0.0.3 (based on code in repos)

## Build

```bash
docker build -t happy-tools:0.0.3 .
```

## Local

### Deploy

* Log into https://aml-repo.cms.waikato.ac.nz with user that has write access

  ```bash
  docker login -u USER public-push.aml-repo.cms.waikato.ac.nz:443
  ```

* Execute commands

  ```bash
  docker tag \
      happy-tools:0.0.3 \
      public-push.aml-repo.cms.waikato.ac.nz:443/wairas/happy-tools:0.0.3
      
  docker push public-push.aml-repo.cms.waikato.ac.nz:443/wairas/happy-tools:0.0.3
  ```

### Use

* Log into https://aml-repo.cms.waikato.ac.nz with public/public credentials for read access

  ```bash
  docker login -u public --password public public.aml-repo.cms.waikato.ac.nz:443
  ```

* Use image

  ```bash
  docker run -u $(id -u):$(id -g) \
      -v /local/dir:/workspace \
      -it public.aml-repo.cms.waikato.ac.nz:443/wairas/happy-tools:0.0.3
  ```

**NB:** Replace `/local/dir` with a local directory that you want to map inside the container. 
For the current directory, simply use `pwd`.


## Docker hub

### Deploy

* Log into docker hub as user `waikatohappy`:

  ```bash
  docker login -u waikatohappy
  ```

* Execute command:

  ```bash
  docker tag \
      happy-tools:0.0.3 \
      waikatohappy/happy-tools:0.0.3
  
  docker push waikatohappy/happy-tools:0.0.3
  ```

### Use

```bash
docker run -u $(id -u):$(id -g) \
    -v /local/dir:/workspace \
    -it waikatohappy/happy-tools:0.0.3
```

**NB:** Replace `/local/dir` with a local directory that you want to map inside the container. 
For the current directory, simply use `pwd`.
