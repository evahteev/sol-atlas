# Step 1: Build the image using the official Node.js base image
FROM docker-registry.dexguru.biz/dex.guru/utils/node:21-alpine as builder

# Set the working directory inside the container
WORKDIR /app

# Copy the package.json and package-lock.json (or yarn.lock) files into the working directory
COPY src/prisma ./src/prisma
COPY package.json ./
COPY yarn.lock ./
COPY next.config.mjs ./

# Install dependencies
RUN yarn install
RUN yarn prisma generate


# Copy the rest of your application's source code into the working directory
COPY . .


# i.e. in gitlab-ci.yml pass --build-arg CAMUNDA_URL="https://chainflow-keeper.dexguru.biz/engine-rest"
ARG CAMUNDA_URL
ENV CAMUNDA_URL=$CAMUNDA_URL

ARG SYS_KEY
ENV SYS_KEY=$SYS_KEY

ARG BOT_URL
ENV BOT_URL=$BOT_URL

ARG AUTH_SECRET
ENV AUTH_SECRET=$AUTH_SECRET

ARG AUTH_URL
ENV AUTH_URL=$AUTH_URL

ARG DATABASE_URL
ENV DATABASE_URL=$DATABASE_URL

ARG POSTGRES_USER
ENV POSTGRES_USER=$POSTGRES_USER

ARG POSTGRES_PASSWORD
ENV POSTGRES_PASSWORD=$POSTGRES_PASSWORD

ARG POSTGRES_DB
ENV POSTGRES_DB=$POSTGRES_DB

ARG DEPLOY_ENVIRONMENT
ENV DEPLOY_ENVIRONMENT=$DEPLOY_ENVIRONMENT

ENV AUTH_TRUST_HOST=true

# Build your Next.js application
RUN yarn build

# Step 2: Run the built application using a lightweight Node.js image
FROM node:21-alpine

WORKDIR /app

COPY package.json ./
COPY yarn.lock ./

# Copy the built application from the previous stage
# Uncomment or add the next.config.js file copy command if necessary and present
# COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/next.config.mjs ./

# Expose the port your app runs on
EXPOSE 3000

# Command to run your app
CMD ["yarn", "start"]
