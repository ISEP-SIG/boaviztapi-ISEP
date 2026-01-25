<div align="center">
  <table border="0">
    <tr>
      <td align="center" valign="middle" width="33%">
        <img src="https://github.com/ISEP-SIG/boaviztapi-ISEP/blob/main/boaviztapi_color.svg" alt="BoaviztAPI" width="150">
      </td>
      <td align="center" valign="middle" width="33%">
        <img src="https://github.com/ISEP-SIG/boaviztapi-ISEP/blob/main/electricitymaps_logo.avif" alt="ElectricityMaps" width="150">
      </td>
      <td align="center" valign="middle" width="33%">
        <img src="https://github.com/ISEP-SIG/boaviztapi-ISEP/blob/main/leaner_cloud_logo.png" alt="LeanerCloud" width="150">
      </td>
    </tr>
  </table>
</div>

<h3 align="center">
   An extended API based on <a href="https://boavizta.cmakers.io/">Boavizta's</a> methodologies and data, integrated with <a href="https://www.electricitymaps.com/">ElectricityMap's</a>
   pricing and green energy API and <a href="https://github.com/LeanerCloud/ec2-instances-info">Leaner Cloud's Vantage based fork</a> for cloud instance pricing data
</h3>

---

See the [documentation](https://doc.api.boavizta.org/) for <a href="https://boavizta.cmakers.io/">Boavizta's</a> API usage and methodology.

[![Python tests](https://github.com/ISEP-SIG/boaviztapi-ISEP/actions/workflows/test.yml/badge.svg)](https://github.com/ISEP-SIG/boaviztapi-ISEP/actions/workflows/test.yml)

<h3> Special thanks to the following projects </h3>

💬 [Join Boavizta's community on their public chat](https://chat.boavizta.org/signup_user_complete/?id=97a1cpe35by49jdc66ej7ktrjc) <br>
🤝🏼 [Contribute to Electricity Maps' open-source dashboard project](https://github.com/electricitymaps/electricitymaps-contrib) <br>
🎉 [Special thanks to LeanerCloud for offering a data dump for cloud instance pricing](https://github.com/LeanerCloud/ec2-instances-info)
---


## :dart: Objective

<b>Visit <a href=https://github.com/Boavizta/boaviztapi/tree/main>Boavizta's Github page</a> to explore their documentation and objective.</b>

## :fast_forward: Test it yourself (no installation)

* See our front-end app (using the extended API): <https://isepfrontend.duckdns.org>

* See the OpenAPI specification: <https://isepbackend.duckdns.org>

## Run a local instance

### :whale: Run backend API using Docker Compose

<p>The backend is available as a standalone docker container that exposes an OpenAPI documentation page and the
REST API endpoints for all the features used in the dashboard. The backend requires an open MongoDB connection
to store user configurations and portfolios.</p>

```yaml
services:

  mongodb:
    image: mongo:8.2.3
    ports:
      - "27017:27017"
    volumes:
      - mongodb_volume:/data/db
    networks:
      default:
        aliases:
          - mongodb

  backend:
    restart: on-failure:2
    pull_policy: always
    build:
      context: .
      dockerfile: Dockerfile
    env_file:
      - path: .env.docker
        required: true
    ports:
      - "5000:5000"
    expose:
      - 5000
    depends_on:
      - mongodb
    networks:
      - default



volumes:
  mongodb_volume:

networks:
  default:

```
Use the above docker-compose file and start the services. Make sure to have a `.env` file with all the necessary
API keys needed for the backend to function as expected. You can find an example environment file named `.env.sample`.
The backend logs will specifically throw an error for each missing  environment variable, or it will shut down if no
MongoDB connection is established.

```bash
docker compose up -d
```
The backend will be accessible at <http://localhost:5000>

### :whale: Run the entire application (backend, frontend and database) using Docker Compose

<p>The backend API has an accompanying frontend. To run the entire application, use the Docker Compose script found
in the repository. We recommend using Docker Swarm or Kubernetes Secrets to make all the necessary environment variables
(for both frontend and backend) available to the services. They can also be inserted by setting system-wide environment
variables on the hosting machine through a terminal. To see a list of the environment variables used also by the
frontend, check the following file in the frontend repository:</p>
<a href="https://github.com/ISEP-SIG/ISEP-Frontend/blob/main/.env.sample">ISEP-Frontend .env.sample file</a>

## :computer: Development

### Prerequisite

Python 3 mandatory, Python >=3.10 and [Poetry](https://python-poetry.org/) strongly recommended.

### Setup poetry

Install poetry (see the [install instructions](https://python-poetry.org/docs/) for more details):

```bash
$ pip3 install poetry
```

Install dependencies and create a Python virtual environment:

```bash
$ make install
$ poetry shell
```

### Launch a development server

**Once in the poetry environment**

The development server uses [uvicorn](https://www.uvicorn.org/) and [FastAPI](https://fastapi.tiangolo.com/). You can launch the development server with the `uvicorn` CLI.

```bash
$ uvicorn boaviztapi.main:app --host=localhost --port 5000
```

You can run the tests with `pytest` via `make test`.

### Create your own docker image and run it

Build application package:

```sh
make install
```

Build Docker image:

```sh
# using the makefile (recommended)
make docker-build

# manual build (requires to set version)
docker build --build-arg VERSION=`poetry version -s` .
```

Run Docker image:

```sh
docker run -p 5000:5000/tcp boavizta/boaviztapi:`poetry version -s`
```

#### Alternative (if you don't have Python or Poetry)

```sh
make docker-build-development

make docker-run-development
```



### OpenAPI specification (Swagger)

Once API server is launched API swagger is available at [https://localhost:5000/docs](https://localhost:5000/docs).

## 🔒 Authentication settings
Our backend and frontend use an OAuth-based authentication method. To find out more information on how to use these
authentication methods on your own deployment, please check out this documentation file: [oauth.md](docs/oauth.md)

## :scroll: License

GNU Affero General Public License v3.0
