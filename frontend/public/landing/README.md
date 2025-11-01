# SOL Atlas - Solana Ecosystem Support & Knowledge Assistant

A comprehensive landing page for SOL Atlas, the Solana ecosystem support and knowledge layer that can be embedded on any dApp. Built on the GURU Framework with fast, privacy-aware LLM and beautiful, adoptable UI.

## 🗺️ Overview

SOL Atlas is an intelligent support assistant specifically designed for Solana dApps. It combines your documentation, community chats, FAQs, and on-chain context with the broader SOL ecosystem directory to provide reliable answers, live context, and clean escalation to your team.

## ✨ Key Features

### 🧠 Intelligent Knowledge Base
- **Unified Sources**: Merge docs, change logs, FAQs, and community answers
- **Freshness Indicators**: "Last updated" timestamps and source badges
- **Ecosystem Integration**: Curated & verified links for explorers, wallets, DeFi tools

### 🔗 On-chain Awareness
- **Real-time Data**: Address health, transaction status, token metadata, program IDs
- **Risk Detection**: Known scam lists, duplicated tickers, revoked authorities
- **Deep Links**: Direct integration with SolanaFM, Solscan, Helius, Phantom, Jupiter

### 💬 Intercom-style Assistant
- **Multiple Embed Modes**: Widget, sidebar, or full-page assistant
- **Smart Escalation**: Role-based routing with full conversation context
- **Community Integration**: Discord/Telegram webhook support

### 🎨 Adoptable UI
- **Brand Theming**: Custom colors, logos, dark/light modes
- **Responsive Design**: Works on all devices and screen sizes
- **Accessibility**: WCAG 2.1 AA compliant with keyboard navigation

### 📊 Analytics & Insights
- **Usage Metrics**: Top questions, deflection rates, escalation reasons
- **Performance Tracking**: Response times, satisfaction scores
- **Actionable Insights**: Identify knowledge gaps and improvement opportunities

## 🚀 Quick Start

### Installation

1. **Add Script**: Include our JavaScript SDK in your dApp
2. **Connect Sources**: Link docs, Discord, Telegram (read-only access)
3. **Choose Providers**: Select on-chain data providers (Helius, QuickNode, etc.)
4. **Theme**: Customize colors, logo, and tone to match your brand
5. **Go Live**: Deploy and start helping users immediately

### Basic Integration

```html
<!-- Include SOL Atlas SDK -->
<script src="https://cdn.solatlas.com/sdk.js"></script>

<!-- Initialize SOL Atlas -->
<script>
  SOLAtlas.init({
    apiKey: 'your-api-key',
    sources: {
      docs: 'https://your-docs.com',
      discord: 'your-discord-channel-id',
      telegram: 'your-telegram-bot-token'
    },
    onchain: {
      rpc: 'https://your-rpc-endpoint.com',
      explorer: 'solanafm'
    },
    theme: {
      primary: '#9945ff',
      secondary: '#14f195',
      logo: 'https://your-logo.com/logo.png'
    }
  });
</script>
```

## 🛠️ Technical Stack

- **Frontend**: Vanilla HTML/CSS/JavaScript with modern ES6+ features
- **Design System**: Custom CSS variables and utility classes
- **Responsive**: Mobile-first design with CSS Grid and Flexbox
- **Accessibility**: ARIA labels, keyboard navigation, screen reader support
- **Performance**: Optimized assets, lazy loading, minimal dependencies

## 🎨 Design System

### Color Palette
- **Primary**: Solana Purple (#9945ff)
- **Secondary**: Solana Green (#14f195)
- **Accent**: Teal (#00d4aa)
- **Success**: Green (#38a169)
- **Warning**: Orange (#ed8936)
- **Danger**: Red (#e53e3e)

### Typography
- **Font Family**: System fonts for optimal performance
- **Scale**: 12px to 60px with consistent ratios
- **Weights**: 400 (normal), 500 (medium), 600 (semibold), 700 (bold)

### Components
- **Buttons**: Primary, secondary, accent variants with hover states
- **Cards**: Elevated containers with subtle shadows
- **Badges**: Source chips, status indicators, verification badges
- **Alerts**: Info, success, warning, danger states
- **Forms**: Inputs, selects, textareas with focus states

## 📱 Responsive Design

The landing page is fully responsive with breakpoints at:
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: 1024px - 1280px
- **Large Desktop**: > 1280px

## ♿ Accessibility

- **WCAG 2.1 AA Compliant**: Meets accessibility standards
- **Keyboard Navigation**: Full keyboard support for all interactive elements
- **Screen Reader Support**: Proper ARIA labels and semantic HTML
- **High Contrast**: Support for high contrast mode
- **Reduced Motion**: Respects user's motion preferences

## 🔒 Security & Privacy

- **Read-only Access**: Sources are accessed in read-only mode by default
- **Data Privacy**: PII masking and granular privacy controls
- **Secure APIs**: All on-chain lookups proxied through secure endpoints
- **Audit Trail**: Full logging of admin actions and data access
- **GDPR Compliant**: Export and delete functionality for user data

## 🌐 Browser Support

- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile**: iOS Safari 14+, Chrome Mobile 90+
- **Progressive Enhancement**: Graceful degradation for older browsers

## 📊 Performance

- **Lighthouse Score**: 95+ across all metrics
- **Core Web Vitals**: Optimized for LCP, FID, and CLS
- **Bundle Size**: Minimal JavaScript footprint
- **Loading Speed**: < 2s initial page load on 3G

## 🚀 Deployment

### Static Hosting
The landing page can be deployed to any static hosting service:
- **Vercel**: `vercel --prod`
- **Netlify**: Drag and drop the `dist` folder
- **GitHub Pages**: Push to `gh-pages` branch
- **AWS S3**: Upload files to S3 bucket with static hosting

### Docker
```bash
# Build the image
docker build -t sol-atlas-landing .

# Run the container
docker run -p 80:80 sol-atlas-landing
```

### Kubernetes
```bash
# Apply the Kubernetes manifests
kubectl apply -f k8s/
```

## 📈 Analytics

Track key metrics with built-in analytics:
- **Page Views**: Total and unique visitors
- **Engagement**: Time on page, scroll depth
- **Conversions**: CTA clicks, demo interactions
- **Performance**: Core Web Vitals, error rates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.solatlas.com](https://docs.solatlas.com)
- **Community**: [Discord](https://discord.gg/solatlas)
- **Email**: support@solatlas.com
- **GitHub Issues**: [Report bugs or request features](https://github.com/solatlas/landing/issues)

## 🙏 Acknowledgments

- Built on the [GURU Framework](https://guruframework.com)
- Inspired by the Solana ecosystem and community
- Design system based on modern web standards
- Accessibility guidance from WCAG 2.1 guidelines

---

**SOL Atlas** - The Solana ecosystem support & knowledge layer, embedded on your site.

Built with ❤️ for the Solana community.
