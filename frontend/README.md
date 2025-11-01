# Telegram Mini Apps Next.js Template

This template demonstrates how developers can implement a web application on the Telegram
Mini Apps platform using the following technologies and libraries:

- [Next.js](https://nextjs.org/)
- [TypeScript](https://www.typescriptlang.org/)
- [TON Connect](https://docs.ton.org/develop/dapps/ton-connect/overview)
- [@telegram-apps SDK](https://docs.telegram-mini-apps.com/packages/telegram-apps-sdk)
- [Telegram UI](https://github.com/Telegram-Mini-Apps/TelegramUI)

> The template was created using [pnpm](https://pnpm.io/). Therefore, it is required to use
> it for this project as well. Using other package managers, you will receive a corresponding error.

## Install Dependencies

If you have just cloned this template, you should install the project dependencies using the
command:

```Bash
pnpm install
```

## Scripts

This project contains the following scripts:

- `dev`. Runs the application in development mode.
- `dev:https`. Runs the application in development mode using self-signed SSL certificate.
- `build`. Builds the application for production.
- `start`. Starts the Next.js server in production mode.
- `lint`. Runs [eslint](https://eslint.org/) to ensure the code quality meets the required
  standards.

To run a script, use the `pnpm run` command:

```Bash
pnpm run {script}
# Example: pnpm run build
```

## Create Bot and Mini App

Before you start, make sure you have already created a Telegram Bot. Here is
a [comprehensive guide](https://docs.telegram-mini-apps.com/platform/creating-new-app) on how to
do it.

## Run

Although Mini Apps are designed to be opened
within [Telegram applications](https://docs.telegram-mini-apps.com/platform/about#supported-applications),
you can still develop and test them outside of Telegram during the development process.

To run the application in the development mode, use the `dev` script:

```bash
pnpm run dev
```

After this, you will see a similar message in your terminal:

```bash
▲ Next.js 14.2.3
- Local:        http://localhost:3000

✓ Starting...
✓ Ready in 2.9s
```

To view the application, you need to open the `Local`
link (`http://localhost:3000` in this example) in your browser.

It is important to note that some libraries in this template, such as `@telegram-apps/sdk`, are not
intended for use outside of Telegram.

Nevertheless, they appear to function properly. This is because the `src/hooks/useTelegramMock.ts`
file, which is imported in the application's `Root` component, employs the `mockTelegramEnv`
function to simulate the Telegram environment. This trick convinces the application that it is
running in a Telegram-based environment. Therefore, be cautious not to use this function in
production mode unless you fully understand its implications.

### Run Inside Telegram

Existing bot:

yarn dev:https
@overmindit_bot

Make local certs

to get localhost-key.pem
and localhost.pem

```bash
brew install mkcert
mkcert -install
mkcert localhost

```

If you get Sign In failed: Credentiols Sign In there is no connection to flow api, check your envs.

New one:

You need to create a Telegram Bot and Register the Mini App
Create a Telegram Bot:

Open Telegram and search for the BotFather.
Start a chat with BotFather and use the /newbot command.
Follow the prompts to name your bot and get the bot token.
Register a Telegram Mini App:

In the same chat with BotFather, use the /newapp command.
Link the newly created Mini App to your bot.
You will receive a direct link to your Mini App in the format: https://t.me/{mybot}/{myapp}.

https://medium.com/@calixtemayoraz/step-by-step-guide-to-build-a-telegram-chatbot-with-a-simple-webapp-ui-using-python-44dca453522f

Although it is possible to run the application outside of Telegram, it is recommended to develop it
within Telegram for the most accurate representation of its real-world functionality.

To run the application inside Telegram, [@BotFather](https://t.me/botfather) requires an HTTPS link.

This template already provides a solution.

To retrieve a link with the HTTPS protocol, consider using the `dev:https` script:

```bash
$ pnpm run dev:https

▲ Next.js 14.2.3
- Local:        https://localhost:3000

✓ Starting...
✓ Ready in 2.4s
```

Visiting the `Local` link (`https://localhost:3000` in this example) in your
browser, you will see the following warning:

![SSL Warning](assets/ssl-warning.png)

This browser warning is normal and can be safely ignored as long as the site is secure. Click
the `Proceed to localhost (unsafe)` button to continue and view the application.

Once the application is displayed correctly, submit this link as the Mini App link
to [@BotFather](https://t.me/botfather). Then, navigate
to [https://web.telegram.org/k/](https://web.telegram.org/k/), find your bot, and launch the
Telegram Mini App. This approach provides the full development experience.

## Deploy

The easiest way to deploy your Next.js app is to use
the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme)
from the creators of Next.js.

Check out the [Next.js deployment documentation](https://nextjs.org/docs/deployment) for more
details.

## Useful Links

- [Platform documentation](https://docs.telegram-mini-apps.com/)
- [@telegram-apps/sdk-react documentation](https://docs.telegram-mini-apps.com/packages/telegram-apps-sdk-react)
- [Telegram developers community chat](https://t.me/devs)

# File Upload Support

The application supports file uploads through the `FormFieldFile` component. Files are uploaded server-side to AWS S3 to avoid CORS issues.

### Environment Variables Required

Add these to your `.env.local`:

```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_S3_BUCKET_NAME=your-bucket-name

# S3 Public URL (for accessing uploaded files)
NEXT_PUBLIC_S3_BASE_URL=https://your-bucket-name.s3.amazonaws.com
```

### Usage

```tsx
import { FormFieldFile } from '@/components/composed/FormField/FormFieldFile'

// In your form component

;<FormFieldFile
  caption="Upload File"
  autoUpload={true} // Automatically upload when file is selected
  onValueChange={(uploadUrls) => {
    // uploadUrls will be an array of S3 URLs
    console.log('Uploaded files:', uploadUrls)
  }}
/>
```

### How it Works

1. User selects a file using the file input
2. File is automatically uploaded to your Next.js API endpoint (`/api/upload`)
3. The API uploads the file to S3 server-side
4. Returns the public S3 URL for the uploaded file
5. The URL is passed to your form's `onValueChange` callback

### File Naming

Files are stored with UUID-based names in the format: `uploads/{userId}/{uuid}.{extension}`

This ensures:

- Unique file names to prevent conflicts
- User-specific upload directories
- Clean, predictable URLs
