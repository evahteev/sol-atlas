import { Address, Hex, createPublicClient, http } from 'viem'
import { mainnet } from 'viem/chains'

const publicClient = createPublicClient({
  chain: mainnet,
  transport: http(),
})

/**
 * Handles POST requests for verifying a signed Ethereum message signed by either a Smart Contract Account or Externally Owned Account.
 *
 * @param {Request} request - The incoming HTTP request containing JSON data.
 * @returns {Promise<Response>} A JSON response indicating whether the signature is valid.
 *
 * Expected Request Body:
 * ```json
 * {
 *   "address": "0x123...",
 *   "message": "Hello, world!",
 *   "signature": "0xabc..."
 * }
 * ```
 *
 * @throws {Response} Returns 400 if validation fails, 500 if an unexpected error occurs.
 */
export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { address, message, signature } = body

    if (!address || typeof address !== 'string') {
      return new Response(JSON.stringify({ error: 'Invalid address' }), { status: 400 })
    }
    if (!message || typeof message !== 'string') {
      return new Response(JSON.stringify({ error: 'Invalid message' }), { status: 400 })
    }
    if (!signature || typeof signature !== 'string') {
      return new Response(JSON.stringify({ error: 'Invalid signature' }), { status: 400 })
    }
    const valid = await publicClient.verifyMessage({
      address: address as Address,
      message,
      signature: signature as Hex,
    })
    return Response.json({ valid })
  } catch (e) {
    return new Response(`Verify Signature error: ${JSON.stringify(e)}`, { status: 500 })
  }
}
