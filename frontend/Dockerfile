# Step 1: Build the image using the official Node.js base image
FROM docker-registry.dexguru.biz/dex.guru/utils/node:22-alpine as builder

# Install necessary build tools, including kernel headers
RUN apk add --no-cache git python3 make g++ linux-headers eudev-dev && ln -sf /usr/bin/python3 /usr/bin/python

ARG NEXT_PUBLIC_GIT_COMMIT
ENV NEXT_PUBLIC_GIT_COMMIT=$NEXT_PUBLIC_GIT_COMMIT

ARG NEXT_PUBLIC_CI_PROJECT_NAME
ENV NEXT_PUBLIC_CI_PROJECT_NAME=$NEXT_PUBLIC_CI_PROJECT_NAME

# Set the working directory inside the container
WORKDIR /app

# Copy the package.json and package-lock.json (or yarn.lock) files into the working directory
COPY package.json ./
COPY yarn.lock ./
COPY next.config.ts ./

# Copy the .git directory into the build stage to allow git commands
COPY .git .git

# Install dependencies
RUN yarn install

# Copy the rest of your application's source code into the working directory
COPY . .

# Build your Next.js application
RUN yarn build

# Step 2: Run the built application using a lightweight Node.js image
FROM docker-registry.dexguru.biz/dex.guru/utils/node:22-alpine

# Install git in the builder stage
RUN apk add --no-cache git curl jq

WORKDIR /app

COPY package.json ./
COPY yarn.lock ./
# Copy the .git directory into the build stage to allow git commands
COPY .git .git

# Copy the built application from the previous stage
# Uncomment or add the next.config.js file copy command if necessary and present
# COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/next.config.ts ./

# Expose the port your app runs on
EXPOSE 3000

# Command to run your app
CMD ["yarn", "start"]
