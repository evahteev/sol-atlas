# Community Onboarding System

## Overview

The Community Onboarding System is a flexible, reusable onboarding flow designed for community applications. Unlike the Utopia-specific onboarding, this system uses dynamic variables to customize the experience for any community while maintaining a clean, modern interface focused on community features and bot integration.

## Key Features

- **Dynamic Community Branding**: Uses variables for community name, description, and social links
- **Bot-Centric Experience**: Focuses on bot features and community assistance rather than financial features
- **Group Integration**: Automatically displays and links to community groups
- **Simplified Flow**: Streamlined process without complex reward systems
- **Mobile-Responsive Design**: Clean, modern UI that works on all devices
- **No Platform Lock-in**: Generic community features without Utopia-specific branding

## Process Variables

### Required Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `community_name` | String | Name of the community | "Tech Innovators" |
| `community_description` | String | Community description | "A community for tech enthusiasts and innovators" |
| `bot_name` | String | Primary bot username (without @) | "TechInnovatorsBot" |

### Optional Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `social_discord` | String | Discord server invite link | "https://discord.gg/xyz" |
| `social_telegram` | String | Telegram group/channel link | "https://t.me/techinnovators" |
| `social_twitter` | String | Twitter/X profile link | "https://twitter.com/techinnovators" |

### Group Variables (up to 3 groups)

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `group_1_name` | String | First group name | "General Discussion" |
| `group_1_link` | String | First group join link | "https://t.me/joinchat/xyz" |
| `group_1_description` | String | First group description | "Main community discussions" |
| `group_2_name` | String | Second group name | "Developers" |
| `group_2_link` | String | Second group join link | "https://t.me/joinchat/abc" |
| `group_2_description` | String | Second group description | "For developers and coders" |
| `group_3_name` | String | Third group name | "Announcements" |
| `group_3_link` | String | Third group join link | "https://t.me/joinchat/def" |
| `group_3_description` | String | Third group description | "Important updates and news" |

### Bot Variables (up to 2 additional bots)

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `bot_1_name` | String | First additional bot name | "Support Bot" |
| `bot_1_handle` | String | First bot handle (without @) | "TechSupportBot" |
| `bot_1_description` | String | First bot description | "Get technical support" |
| `bot_2_name` | String | Second additional bot name | "News Bot" |
| `bot_2_handle` | String | Second bot handle (without @) | "TechNewsBot" |
| `bot_2_description` | String | Second bot description | "Latest tech news updates" |

## Form Structure

### 1. Landing Page (`0_community_landing.form`)
- **Purpose**: Welcome users and show community information
- **Features**: Dynamic community info, social links, call-to-action
- **Variables Used**: `community_name`, `community_description`, social links, `bot_name`

### 2. Welcome & Discover (`1_community_welcome_discover.form`)
- **Purpose**: Introduce community platform features
- **Features**: Feature overview, journey preview, setup options
- **Variables Used**: `community_name`

### 3. Bot Connection (`2.1_community_bot_connect.form`)
- **Purpose**: Connect users to the community bot
- **Features**: Bot information, connection instructions, feature preview
- **Variables Used**: `bot_name`, `community_name`

### 4. Verification Code (`2.2_community_confirmation_code.form`)
- **Purpose**: Verify Telegram bot connection
- **Features**: Code input, instructions, retry options
- **Variables Used**: None (uses Camunda verification process)

### 5. Bot Success (`2.3_community_bot_success.form`)
- **Purpose**: Confirm successful bot connection
- **Features**: Success celebration, next steps, feature unlocks
- **Variables Used**: `community_name`, `bot_name`

### 6. Bot Features (`3_community_bot_features.form`)
- **Purpose**: Explain bot capabilities and commands
- **Features**: Feature cards, command examples, usage tips
- **Variables Used**: `community_name`, `bot_name`

### 7. Final Welcome (`4_community_welcome_complete.form`)
- **Purpose**: Complete onboarding with group/bot joining
- **Features**: Group cards, bot links, next steps
- **Variables Used**: All community, group, and bot variables

## BPMN Process Flow

The `community_onboarding.bpmn` process includes:

1. **Start**: Landing page with community information
2. **Welcome**: Feature discovery with skip option
3. **Bot Setup**: Optional bot connection flow
4. **Verification**: Telegram code verification (if bot setup chosen)
5. **Features**: Bot feature explanation
6. **Complete**: Final welcome with groups and bots

### Decision Points

- **Continue vs Skip**: Users can skip bot setup and go directly to completion
- **Verification Retry**: Failed verification allows retry attempts
- **Flexible Groups**: Shows only configured groups (1-3 groups supported)
- **Dynamic Bots**: Displays configured bots with fallback defaults

## Usage Examples

### Basic Community Setup

```javascript
{
  "community_name": "AI Enthusiasts",
  "community_description": "A community for AI researchers and enthusiasts",
  "bot_name": "AIEnthusiastsBot",
  "social_telegram": "https://t.me/aienthusiasts",
  "social_discord": "https://discord.gg/ai-enthusiasts",
  "group_1_name": "General Discussion",
  "group_1_link": "https://t.me/joinchat/ai-general",
  "group_1_description": "General AI discussions and news"
}
```

### Full Community Setup

```javascript
{
  "community_name": "Startup Founders Network",
  "community_description": "Connecting startup founders worldwide",
  "bot_name": "StartupNetworkBot",
  "social_telegram": "https://t.me/startupfounders",
  "social_discord": "https://discord.gg/startup-network",
  "social_twitter": "https://twitter.com/startupnetwork",
  "group_1_name": "General Networking",
  "group_1_link": "https://t.me/joinchat/startup-general",
  "group_1_description": "Connect with fellow founders",
  "group_2_name": "Funding & Investment",
  "group_2_link": "https://t.me/joinchat/startup-funding",
  "group_2_description": "Discuss funding opportunities",
  "group_3_name": "Product Development",
  "group_3_link": "https://t.me/joinchat/startup-product",
  "group_3_description": "Product development discussions",
  "bot_1_name": "Mentor Bot",
  "bot_1_handle": "StartupMentorBot",
  "bot_1_description": "Connect with mentors and advisors",
  "bot_2_name": "Resources Bot",
  "bot_2_handle": "StartupResourcesBot",
  "bot_2_description": "Access startup resources and tools"
}
```

## Technical Requirements

### Service Tasks

The process requires these Camunda service delegates:

- `SetStartVariablesListener`: Initialize process variables
- `SendTelegramVerificationDelegate`: Send verification codes
- `VerifyTelegramCodeDelegate`: Verify user input codes

### Form Integration

- Forms use Camunda form variables (`cam-variable-name`, `cam-variable-type`)
- AngularJS templating for dynamic content (`{{ variable_name }}`)
- Conditional display with `ng-if` directives
- Responsive CSS with mobile-first design

## Customization

### Styling

The system uses consistent CSS custom properties that can be easily modified:

- Primary colors: Purple/Blue gradient theme
- Success colors: Green gradient theme
- Background: Dark theme with cards
- Typography: Space Grotesk font family

### Adding More Groups/Bots

To support more than 3 groups or 2 additional bots:

1. Add new variables to the BPMN process
2. Update the final welcome form template
3. Add corresponding input parameters in the BPMN

### Localization

Forms can be localized by:

1. Replacing hardcoded text with template variables
2. Adding language variables to the process
3. Using conditional templates based on language selection

## Deployment

1. Place all files in `engine/src/main/resources/utopia-app/onboarding_community/`
2. Deploy the BPMN process to Camunda
3. Configure process variables when starting new instances
4. Ensure required service delegates are available

## Fallback Behavior

The system gracefully handles missing variables:

- **Community Info**: Uses generic defaults if variables not provided
- **Groups**: Shows "Coming Soon" cards if no groups configured
- **Bots**: Displays placeholder bots if none configured
- **Social Links**: Hides social buttons if links not provided

This ensures the onboarding works even with minimal configuration. 