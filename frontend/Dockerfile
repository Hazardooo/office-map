FROM node:24-alpine

WORKDIR /app

# Copy package.json
COPY package.json ./

RUN npm config set strict-ssl false

# Install dependencies
RUN npm install

# Copy the rest of the application files
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
