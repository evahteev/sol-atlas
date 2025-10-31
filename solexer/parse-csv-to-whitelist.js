/**
 * Parse CSV to Whitelist
 * 
 * Extracts Solana token addresses from CoinGecko CSV export
 * and creates a whitelist.txt file with one address per line.
 * 
 * Usage:
 *   node parse-csv-to-whitelist.js
 */

const fs = require('fs');
const path = require('path');

const CSV_FILE = 'SOLANA_tokens_2025_10_23.csv';
const OUTPUT_FILE = 'whitelist.txt';

function parseCsvLine(line) {
    const fields = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        
        if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
            fields.push(current);
            current = '';
        } else {
            current += char;
        }
    }
    fields.push(current);
    
    return fields;
}

function extractSolanaAddress(contractAddress) {
    // Contract address field format examples:
    // - "0x69420e3a3aa9e17dea102bb3a9b3b73dcddb9528" (Ethereum only)
    // - "ACWJRei2VGU4tru1oxKHnfoJ3iachwpTeXfEPUNg5Tv" (Solana only)
    // - Multi-chain can be in other columns
    
    if (!contractAddress) {
        return null;
    }
    
    // If it starts with 0x, it's not a Solana address
    if (contractAddress.startsWith('0x')) {
        return null;
    }
    
    // Solana addresses are base58 encoded, typically 32-44 characters
    // and contain only base58 characters (no 0, O, I, l)
    const base58Regex = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;
    
    if (base58Regex.test(contractAddress)) {
        return contractAddress;
    }
    
    return null;
}

function parseJsonField(fieldValue) {
    try {
        // Remove outer quotes if present
        let cleaned = fieldValue.trim();
        if (cleaned.startsWith('"') && cleaned.endsWith('"')) {
            cleaned = cleaned.slice(1, -1);
        }
        
        // Replace escaped quotes
        cleaned = cleaned.replace(/""/g, '"');
        
        return JSON.parse(cleaned);
    } catch (e) {
        return null;
    }
}

function main() {
    console.log('🔍 Parsing Solana tokens from CSV...\n');
    
    const csvPath = path.join(__dirname, CSV_FILE);
    const outputPath = path.join(__dirname, OUTPUT_FILE);
    
    if (!fs.existsSync(csvPath)) {
        console.error(`❌ CSV file not found: ${csvPath}`);
        process.exit(1);
    }
    
    const content = fs.readFileSync(csvPath, 'utf-8');
    const lines = content.split('\n');
    
    console.log(`📄 Total lines in CSV: ${lines.length}`);
    
    // Use a Map to store addresses: lowercase -> original (prefer mixed case)
    const addressMap = new Map();
    let processed = 0;
    let linesWithSolana = 0;
    let rawFound = 0;
    
    // Solana addresses are base58 encoded, 32-44 characters
    // Contains digits 1-9 and letters excluding 0, O, I, l
    const solanaAddressRegex = /\b[1-9A-HJ-NP-Za-km-z]{32,44}\b/g;
    
    // Process each line (skip header)
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        
        processed++;
        
        // Only process lines that mention solana
        if (!line.toLowerCase().includes('solana')) {
            continue;
        }
        
        linesWithSolana++;
        
        // Find all potential Solana addresses in the line
        const matches = line.match(solanaAddressRegex);
        
        if (matches) {
            for (const match of matches) {
                // Filter out Ethereum addresses (40 hex chars) that might match our pattern
                if (match.match(/^[0-9a-f]{40}$/i)) {
                    continue;
                }
                
                // Additional validation: Solana addresses typically start with certain chars
                // and have good base58 character distribution
                const validChars = match.split('').every(c => 
                    '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'.includes(c)
                );
                
                if (validChars && match.length >= 32 && match.length <= 44) {
                    rawFound++;
                    const lower = match.toLowerCase();
                    
                    // Prefer mixed case over lowercase (more likely to be correct)
                    if (!addressMap.has(lower) || match !== lower) {
                        addressMap.set(lower, match);
                    }
                }
            }
        }
        
        // Progress indicator every 1000 lines
        if (processed % 1000 === 0) {
            console.log(`   Processed ${processed} lines, ${linesWithSolana} with Solana, found ${addressMap.size} unique...`);
        }
    }
    
    // Get unique addresses
    const addresses = Array.from(addressMap.values());
    
    console.log(`\n✅ Parsing complete:`);
    console.log(`   - Total tokens processed: ${processed}`);
    console.log(`   - Lines with "solana": ${linesWithSolana}`);
    console.log(`   - Raw addresses found: ${rawFound}`);
    console.log(`   - Unique addresses (deduplicated): ${addresses.length}\n`);
    
    // Write to file
    const sortedAddresses = addresses.sort();
    fs.writeFileSync(outputPath, sortedAddresses.join('\n') + '\n', 'utf-8');
    
    console.log(`💾 Whitelist saved to: ${outputPath}`);
    console.log(`📊 Total unique addresses: ${sortedAddresses.length}\n`);
    
    // Show first 5 addresses as sample
    console.log('📝 Sample addresses (first 5):');
    sortedAddresses.slice(0, 5).forEach((addr, i) => {
        console.log(`   ${i + 1}. ${addr}`);
    });
    
    console.log('\n✨ Done!\n');
}

// Run
try {
    main();
} catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
}

