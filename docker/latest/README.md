# happy-tools latest (based on code in repos)

## Build

```bash
docker build -t happy-tools:latest .
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
      happy-tools:latest \
      public-push.aml-repo.cms.waikato.ac.nz:443/happy/happy-tools:latest
      
  docker push public-push.aml-repo.cms.waikato.ac.nz:443/happy/happy-tools:latest
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
      -it public.aml-repo.cms.waikato.ac.nz:443/happy/happy-tools:latest
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
      happy-tools:latest \
      waikatohappy/happy-tools:latest
  
  docker push waikatohappy/happy-tools:latest
  ```

### Use

```bash
docker run -u $(id -u):$(id -g) \
    -v /local/dir:/workspace \
    -it waikatohappy/happy-tools:latest
```

**NB:** Replace `/local/dir` with a local directory that you want to map inside the container. 
For the current directory, simply use `pwd`.
