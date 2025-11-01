#!/usr/bin/env tsx
/**
 * Internationalization validation script
 * Run this script to validate the i18n implementation
 *
 * Usage: npx tsx scripts/validate-i18n.ts
 */
import fs from 'fs'
import path from 'path'

// Helper to get project root
const getProjectRoot = () => {
  let currentDir = process.cwd()

  // Look for package.json to identify project root
  while (currentDir !== '/') {
    if (fs.existsSync(path.join(currentDir, 'package.json'))) {
      return currentDir
    }
    currentDir = path.dirname(currentDir)
  }

  return process.cwd()
}

const PROJECT_ROOT = getProjectRoot()
const MESSAGES_DIR = path.join(PROJECT_ROOT, 'messages')

interface ValidationResult {
  category: string
  valid: boolean
  issues: string[]
  details?: Record<string, unknown>
}

class I18nValidator {
  private results: ValidationResult[] = []

  async validate(): Promise<ValidationResult[]> {
    console.log('🌐 Starting i18n validation...\n')

    await this.validateMessageFiles()
    await this.validateTranslationConsistency()
    await this.validateMetadataCompleteness()
    await this.validateEnvironmentConfig()
    await this.validateFileStructure()

    return this.results
  }

  private async validateMessageFiles(): Promise<void> {
    console.log('📄 Validating message files...')

    try {
      const locales = ['en', 'ru']
      const messageFiles: Record<string, Record<string, unknown>> = {}

      for (const locale of locales) {
        const filePath = path.join(MESSAGES_DIR, `${locale}.json`)

        if (!fs.existsSync(filePath)) {
          this.addResult('Message Files', false, [`Missing message file: ${locale}.json`])
          continue
        }

        try {
          const content = fs.readFileSync(filePath, 'utf-8')
          messageFiles[locale] = JSON.parse(content)
        } catch (error) {
          this.addResult('Message Files', false, [`Invalid JSON in ${locale}.json: ${error}`])
          continue
        }
      }

      if (Object.keys(messageFiles).length === locales.length) {
        this.addResult('Message Files', true, [], { loadedLocales: Object.keys(messageFiles) })
      }
    } catch (error) {
      this.addResult('Message Files', false, [`Error validating message files: ${error}`])
    }
  }

  private async validateTranslationConsistency(): Promise<void> {
    console.log('🔄 Validating translation consistency...')

    try {
      const enPath = path.join(MESSAGES_DIR, 'en.json')
      const ruPath = path.join(MESSAGES_DIR, 'ru.json')

      if (!fs.existsSync(enPath) || !fs.existsSync(ruPath)) {
        this.addResult('Translation Consistency', false, [
          'Missing message files for consistency check',
        ])
        return
      }

      const enMessages = JSON.parse(fs.readFileSync(enPath, 'utf-8'))
      const ruMessages = JSON.parse(fs.readFileSync(ruPath, 'utf-8'))

      const enKeys = this.getAllKeys(enMessages)
      const ruKeys = this.getAllKeys(ruMessages)

      const missingInRu = enKeys.filter((key) => !ruKeys.includes(key))
      const extraInRu = ruKeys.filter((key) => !enKeys.includes(key))

      const issues: string[] = []
      if (missingInRu.length > 0) {
        issues.push(
          `Keys missing in Russian: ${missingInRu.slice(0, 5).join(', ')}${missingInRu.length > 5 ? ` (and ${missingInRu.length - 5} more)` : ''}`
        )
      }
      if (extraInRu.length > 0) {
        issues.push(
          `Extra keys in Russian: ${extraInRu.slice(0, 5).join(', ')}${extraInRu.length > 5 ? ` (and ${extraInRu.length - 5} more)` : ''}`
        )
      }

      this.addResult('Translation Consistency', issues.length === 0, issues, {
        enKeyCount: enKeys.length,
        ruKeyCount: ruKeys.length,
        missingInRu: missingInRu.length,
        extraInRu: extraInRu.length,
      })
    } catch (error) {
      this.addResult('Translation Consistency', false, [`Error checking consistency: ${error}`])
    }
  }

  private async validateMetadataCompleteness(): Promise<void> {
    console.log('📊 Validating metadata completeness...')

    try {
      const locales = ['en', 'ru']
      const issues: string[] = []

      for (const locale of locales) {
        const filePath = path.join(MESSAGES_DIR, `${locale}.json`)
        if (!fs.existsSync(filePath)) continue

        const messages = JSON.parse(fs.readFileSync(filePath, 'utf-8'))

        // Check Metadata namespace
        if (!messages.Metadata) {
          issues.push(`Missing Metadata namespace in ${locale}`)
          continue
        }

        const metadata = messages.Metadata

        // Check required fields
        const requiredFields = [
          'defaultTitle',
          'defaultDescription',
          'siteTitle',
          'siteDescription',
        ]
        for (const field of requiredFields) {
          if (!metadata[field]) {
            issues.push(`Missing ${field} in ${locale} metadata`)
          }
        }

        // Check pages metadata
        if (!metadata.pages) {
          issues.push(`Missing pages metadata in ${locale}`)
          continue
        }

        const requiredPages = ['aifeed', 'tasks', 'staking', 'tokens', 'swap']
        for (const page of requiredPages) {
          if (!metadata.pages[page]) {
            issues.push(`Missing ${page} page metadata in ${locale}`)
          } else {
            const pageData = metadata.pages[page]
            if (!pageData.title || !pageData.description) {
              issues.push(`Incomplete ${page} page metadata in ${locale}`)
            }
          }
        }
      }

      this.addResult('Metadata Completeness', issues.length === 0, issues)
    } catch (error) {
      this.addResult('Metadata Completeness', false, [`Error validating metadata: ${error}`])
    }
  }

  private async validateEnvironmentConfig(): Promise<void> {
    console.log('⚙️  Validating environment configuration...')

    const issues: string[] = []

    // Check if required environment variables are set (in a typical .env file)
    const envExamplePath = path.join(PROJECT_ROOT, '.env.local.example')
    if (fs.existsSync(envExamplePath)) {
      const envExample = fs.readFileSync(envExamplePath, 'utf-8')
      if (!envExample.includes('NEXT_PUBLIC_DEFAULT_LOCALE')) {
        issues.push('NEXT_PUBLIC_DEFAULT_LOCALE not documented in .env.local.example')
      }
    }

    // Check routing configuration file
    const routingPath = path.join(PROJECT_ROOT, 'src', 'i18n', 'routing.ts')
    if (!fs.existsSync(routingPath)) {
      issues.push('Missing i18n routing configuration file')
    } else {
      const routingContent = fs.readFileSync(routingPath, 'utf-8')
      if (!routingContent.includes('NEXT_PUBLIC_DEFAULT_LOCALE')) {
        issues.push('Routing not using NEXT_PUBLIC_DEFAULT_LOCALE environment variable')
      }
    }

    // Check request configuration
    const requestPath = path.join(PROJECT_ROOT, 'src', 'i18n', 'request.ts')
    if (!fs.existsSync(requestPath)) {
      issues.push('Missing i18n request configuration file')
    }

    this.addResult('Environment Configuration', issues.length === 0, issues)
  }

  private async validateFileStructure(): Promise<void> {
    console.log('📁 Validating file structure...')

    const issues: string[] = []
    const requiredFiles = [
      'src/i18n/routing.ts',
      'src/i18n/request.ts',
      'src/middleware.ts',
      'messages/en.json',
      'messages/ru.json',
    ]

    for (const file of requiredFiles) {
      const filePath = path.join(PROJECT_ROOT, file)
      if (!fs.existsSync(filePath)) {
        issues.push(`Missing required file: ${file}`)
      }
    }

    // Check for i18n utilities
    const utilsDir = path.join(PROJECT_ROOT, 'src', 'utils')
    if (fs.existsSync(utilsDir)) {
      const i18nUtils = ['i18n-performance.ts', 'i18n-dev-tools.ts', 'i18n-testing.ts']

      const existingUtils = i18nUtils.filter((file) => fs.existsSync(path.join(utilsDir, file)))

      if (existingUtils.length > 0) {
        this.addResult('I18n Utilities', true, [], { installedUtils: existingUtils })
      }
    }

    this.addResult('File Structure', issues.length === 0, issues)
  }

  private getAllKeys(obj: Record<string, unknown>, prefix = ''): string[] {
    const keys: string[] = []

    for (const [key, value] of Object.entries(obj)) {
      const fullKey = prefix ? `${prefix}.${key}` : key

      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        keys.push(...this.getAllKeys(value as Record<string, unknown>, fullKey))
      } else {
        keys.push(fullKey)
      }
    }

    return keys
  }

  private addResult(
    category: string,
    valid: boolean,
    issues: string[],
    details?: Record<string, unknown>
  ): void {
    this.results.push({ category, valid, issues, details })

    const status = valid ? '✅' : '❌'
    console.log(`${status} ${category}: ${valid ? 'PASS' : 'FAIL'}`)

    if (!valid && issues.length > 0) {
      issues.forEach((issue) => console.log(`   - ${issue}`))
    }

    if (details) {
      console.log(`   Details:`, details)
    }

    console.log()
  }
}

// Main execution
async function main() {
  const validator = new I18nValidator()
  const results = await validator.validate()

  const totalTests = results.length
  const passedTests = results.filter((r) => r.valid).length
  const failedTests = totalTests - passedTests

  console.log('📋 Validation Summary')
  console.log('===================')
  console.log(`Total tests: ${totalTests}`)
  console.log(`Passed: ${passedTests}`)
  console.log(`Failed: ${failedTests}`)
  console.log(`Success rate: ${((passedTests / totalTests) * 100).toFixed(1)}%`)

  if (failedTests > 0) {
    console.log('\n❌ Issues found:')
    results
      .filter((r) => !r.valid)
      .forEach((result) => {
        console.log(`\n${result.category}:`)
        result.issues.forEach((issue) => console.log(`  - ${issue}`))
      })
    process.exit(1)
  } else {
    console.log('\n🎉 All i18n validation tests passed!')
    process.exit(0)
  }
}

if (require.main === module) {
  main().catch((error) => {
    console.error('❌ Validation failed:', error)
    process.exit(1)
  })
}
