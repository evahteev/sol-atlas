import {createClient} from '@clickhouse/client';
import fs from 'fs';
import path from 'path';
import {CLICKHOUSE_CONFIG} from '../config-solana';

const client = createClient({
    host: CLICKHOUSE_CONFIG.url,
    username: CLICKHOUSE_CONFIG.username,
    password: CLICKHOUSE_CONFIG.password,
    database: CLICKHOUSE_CONFIG.database,
});

// Migration tracking table
const MIGRATIONS_TABLE = `
CREATE TABLE IF NOT EXISTS schema_migrations (
    version String,
    applied_at DateTime DEFAULT now(),
    checksum String
) ENGINE = MergeTree()
ORDER BY applied_at;
`;

async function calculateChecksum(content: string): Promise<string> {
    const crypto = await import('crypto');
    return crypto.createHash('sha256').update(content).digest('hex');
}



export async function runMigrations() {
    try {
        // Create migrations tracking table
        await client.exec({ query: MIGRATIONS_TABLE });
        console.log('Ensured migrations table exists');

        // Get list of applied migrations
        const applied = new Map<string, string>();
        try {
            const appliedMigrations = await client.query({
                query: 'SELECT version, checksum FROM schema_migrations',
                format: 'JSONEachRow',
            });
            
            for await (const row of appliedMigrations.stream()) {
                const rowStr = row.toString();
                if (rowStr.trim()) {
                    const data = JSON.parse(rowStr);
                    applied.set(data.version, data.checksum);
                }
            }
        } catch (error) {
            console.log('No existing migrations found (table empty or doesn\'t exist)');
        }

        // Read migration files from both root and versions subdirectory
        const migrationsDir = path.join(__dirname, '../../db/migrations');
        const versionsDir = path.join(migrationsDir, 'versions');
        
        let files: string[] = [];
        let filePaths: Map<string, string> = new Map();
        
        // Check root migrations directory
        if (fs.existsSync(migrationsDir)) {
            const rootFiles = fs.readdirSync(migrationsDir)
                .filter(f => f.endsWith('.sql'));
            rootFiles.forEach(f => {
                files.push(f);
                filePaths.set(f, path.join(migrationsDir, f));
            });
        }
        
        // Check versions subdirectory
        if (fs.existsSync(versionsDir)) {
            const versionFiles = fs.readdirSync(versionsDir)
                .filter(f => f.endsWith('.sql'));
            versionFiles.forEach(f => {
                files.push(f);
                filePaths.set(f, path.join(versionsDir, f));
            });
        }
        
        files.sort();

        console.log(`Found ${files.length} migration file(s)`);

        for (const file of files) {
            const version = file.replace('.sql', '');
            const filePath = filePaths.get(file)!;
            const content = fs.readFileSync(filePath, 'utf8');
            const checksum = await calculateChecksum(content);

            // Check if already applied
            if (applied.has(version)) {
                const appliedChecksum = applied.get(version);
                if (appliedChecksum !== checksum) {
                    console.warn(`⚠️  Migration ${version} has been modified since it was applied!`);
                    console.warn(`    Applied checksum: ${appliedChecksum}`);
                    console.warn(`    Current checksum: ${checksum}`);
                } else {
                    console.log(`✓ Migration ${version} already applied`);
                }
                continue;
            }

            console.log(`Applying migration: ${version}`);
            
            // Split by semicolons and filter out comments and empty statements
            const statements = content
                .split(';')
                .map(s => s.trim())
                .filter(s => {
                    if (s.length === 0) return false;
                    // Remove SQL comments and check if anything remains
                    const withoutComments = s
                        .split('\n')
                        .filter(line => !line.trim().startsWith('--'))
                        .join('\n')
                        .trim();
                    return withoutComments.length > 0;
                });

            // Execute each statement
            for (let i = 0; i < statements.length; i++) {
                const statement = statements[i].trim();
                if (statement.length === 0) continue;
                    
                try {
                    console.log(`Executing statement: ${statement}`);
                    await client.exec({ query: statement });
                    console.log(`✓ Executed statement ${i + 1}/${statements.length}`);
                } catch (error) {
                    console.error(`Failed to execute statement ${i + 1} in migration ${version}:`);
                    console.error(`Statement: ${statement.substring(0, 200)}...`);
                    throw error;
                }
            }

            // Record migration as applied
            await client.insert({
                table: 'schema_migrations',
                values: [{ version, checksum }],
                format: 'JSONEachRow',
            });

            console.log(`✓ Successfully applied migration: ${version}`);
        }

        console.log('All migrations completed successfully');
    } catch (error) {
        console.error('Migration failed:', error);
        throw error;
    } finally {
        await client.close();
    }
}

// Run migrations if this file is executed directly
if (require.main === module) {
    runMigrations()
        .then(() => {
            console.log('Migration runner completed');
            process.exit(0);
        })
        .catch((error) => {
            console.error('Migration runner failed:', error);
            process.exit(1);
        });
} 