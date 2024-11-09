/**
 * Converts a camelCase string to snake_case.
 *
 * @param key - The camelCase string to convert.
 * @returns The converted snake_case string.
 *
 * @example
 * camelToSnakeCase("firstName"); // Returns "first_name"
 */
function camelToSnakeCase(key: string): string {
  return key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`)
}

/**
 * Transforms the keys of an object from camelCase to snake_case.
 *
 * @param obj - The object with camelCase keys to transform.
 * @returns A new object with keys converted to snake_case.
 *
 * @example
 * const user = {
 *   allowsWriteToPm: true,
 *   firstName: "Andrew",
 *   id: 99281934,
 *   isPremium: true,
 *   languageCode: "en",
 *   lastName: "Rogue",
 *   username: "rogue"
 * };
 * const transformedUser = transformKeysToSnakeCase(user);
 * // Returns {
 * //   allows_write_to_pm: true,
 * //   first_name: "Andrew",
 * //   id: 99281934,
 * //   is_premium: true,
 * //   language_code: "en",
 * //   last_name: "Rogue",
 * //   username: "rogue"
 * // }
 */
export function transformKeysToSnakeCase(obj: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {}

  Object.keys(obj).forEach((key) => {
    const snakeCaseKey = camelToSnakeCase(key)
    result[snakeCaseKey] = obj[key]
  })

  return result
}
