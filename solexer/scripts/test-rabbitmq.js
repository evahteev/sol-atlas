const amqp = require('amqplib');

async function testRabbitMQ() {
    try {
        console.log('Connecting to RabbitMQ...');
        const connection = await amqp.connect(process.env.RABBITMQ_URL || 'amqp://localhost:5672');
        const channel = await connection.createChannel();
        
        const queue = process.env.RABBITMQ_QUEUE || 'block_batches';
        
        // Ensure queue exists
        await channel.assertQueue(queue, { durable: true });
        
        console.log(`Setting up consumer for queue: ${queue}`);
        
        // Consume messages
        channel.consume(queue, (msg) => {
            if (msg) {
                const content = JSON.parse(msg.content.toString());
                console.log('Received message:', JSON.stringify(content, null, 2));
                channel.ack(msg);
            }
        });
        
        console.log('Waiting for messages... Press CTRL+C to exit');
        
        // Keep the script running
        process.on('SIGINT', async () => {
            console.log('\nClosing connection...');
            await channel.close();
            await connection.close();
            process.exit(0);
        });
        
    } catch (error) {
        console.error('Error:', error);
        process.exit(1);
    }
}

testRabbitMQ(); 