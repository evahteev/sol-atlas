"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.runMigrations = runMigrations;
const client_1 = require("@clickhouse/client");
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const config_solana_1 = require("../config-solana");
const client = (0, client_1.createClient)({
    host: config_solana_1.CLICKHOUSE_CONFIG.url,
    username: config_solana_1.CLICKHOUSE_CONFIG.username,
    password: config_solana_1.CLICKHOUSE_CONFIG.password,
    database: config_solana_1.CLICKHOUSE_CONFIG.database,
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
async function calculateChecksum(content) {
    const crypto = await Promise.resolve().then(() => __importStar(require('crypto')));
    return crypto.createHash('sha256').update(content).digest('hex');
}
async function runMigrations() {
    try {
        // Create migrations tracking table
        await client.exec({ query: MIGRATIONS_TABLE });
        console.log('Ensured migrations table exists');
        // Get list of applied migrations
        const applied = new Map();
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
        }
        catch (error) {
            console.log('No existing migrations found (table empty or doesn\'t exist)');
        }
        // Read migration files from both root and versions subdirectory
        const migrationsDir = path_1.default.join(__dirname, '../../db/migrations');
        const versionsDir = path_1.default.join(migrationsDir, 'versions');
        let files = [];
        let filePaths = new Map();
        // Check root migrations directory
        if (fs_1.default.existsSync(migrationsDir)) {
            const rootFiles = fs_1.default.readdirSync(migrationsDir)
                .filter(f => f.endsWith('.sql'));
            rootFiles.forEach(f => {
                files.push(f);
                filePaths.set(f, path_1.default.join(migrationsDir, f));
            });
        }
        // Check versions subdirectory
        if (fs_1.default.existsSync(versionsDir)) {
            const versionFiles = fs_1.default.readdirSync(versionsDir)
                .filter(f => f.endsWith('.sql'));
            versionFiles.forEach(f => {
                files.push(f);
                filePaths.set(f, path_1.default.join(versionsDir, f));
            });
        }
        files.sort();
        console.log(`Found ${files.length} migration file(s)`);
        for (const file of files) {
            const version = file.replace('.sql', '');
            const filePath = filePaths.get(file);
            const content = fs_1.default.readFileSync(filePath, 'utf8');
            const checksum = await calculateChecksum(content);
            // Check if already applied
            if (applied.has(version)) {
                const appliedChecksum = applied.get(version);
                if (appliedChecksum !== checksum) {
                    console.warn(`⚠️  Migration ${version} has been modified since it was applied!`);
                    console.warn(`    Applied checksum: ${appliedChecksum}`);
                    console.warn(`    Current checksum: ${checksum}`);
                }
                else {
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
                if (s.length === 0)
                    return false;
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
                if (statement.length === 0)
                    continue;
                try {
                    console.log(`Executing statement: ${statement}`);
                    await client.exec({ query: statement });
                    console.log(`✓ Executed statement ${i + 1}/${statements.length}`);
                }
                catch (error) {
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
    }
    catch (error) {
        console.error('Migration failed:', error);
        throw error;
    }
    finally {
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
