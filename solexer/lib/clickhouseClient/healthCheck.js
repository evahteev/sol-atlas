"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.waitForClickHouse = waitForClickHouse;
exports.checkClickHouseSchema = checkClickHouseSchema;
const clickhouseClient_1 = require("./clickhouseClient");
async function waitForClickHouse(maxAttempts = 30, delayMs = 2000) {
    console.log('Checking ClickHouse availability...');
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            // Simple query to check if ClickHouse is responding
            await (0, clickhouseClient_1.read)('SELECT 1');
            console.log('✅ ClickHouse is available');
            return;
        }
        catch (error) {
            if (attempt === maxAttempts) {
                console.error('❌ ClickHouse is not available after maximum attempts');
                throw new Error(`ClickHouse health check failed after ${maxAttempts} attempts: ${error.message}`);
            }
            console.warn(`ClickHouse not ready (attempt ${attempt}/${maxAttempts}). Retrying in ${delayMs}ms...`);
            await new Promise(resolve => setTimeout(resolve, delayMs));
        }
    }
}
async function checkClickHouseSchema() {
    console.log('Verifying ClickHouse schema...');
    try {
        // Check if essential tables exist
        const tables = await (0, clickhouseClient_1.read)(`
            SELECT name 
            FROM system.tables 
            WHERE database = currentDatabase() 
            AND name IN ('blocks', 'transactions', 'logs', 'token_transfers', 'native_balances')
            ORDER BY name
        `);
        const expectedTables = ['blocks', 'logs', 'native_balances', 'token_transfers', 'transactions'];
        const existingTables = tables.map((row) => row.name);
        const missingTables = expectedTables.filter(table => !existingTables.includes(table));
        if (missingTables.length > 0) {
            const dbName = await (0, clickhouseClient_1.read)('SELECT currentDatabase()');
            const dbNameStr = dbName.toString();
            throw new Error(`Missing required tables: ${missingTables.join(', ')}. Please run migrations on ${dbNameStr}.`);
        }
        console.log('✅ All required tables are present');
    }
    catch (error) {
        console.error('❌ Schema verification failed:', error.message);
        throw error;
    }
}
