'use client'

import { useLaunchParams } from '@telegram-apps/sdk-react'

/**
 * Restores the original UUID by inserting hyphens at the appropriate positions.
 *
 * UUIDs are typically represented in the following format:
 * xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
 *
 * If a UUID has had its hyphens removed, this function can restore them.
 *
 * Example:
 * Input: "123e4567e89b12d3a456426655440000"
 * Output: "123e4567-e89b-12d3-a456-426655440000"
 *
 * @param uuidWithoutHyphens - The UUID string without hyphens.
 * @returns The restored UUID string with hyphens.
 * @throws Will throw an error if the input length is not 32 characters (the length of a UUID without hyphens).
 */
export function restoreUUID(uuidWithoutHyphens: string): string {
  if (uuidWithoutHyphens.length !== 32) {
    throw new Error('Invalid UUID length. Expected a 32 character string.')
  }

  return `${uuidWithoutHyphens.slice(0, 8)}-${uuidWithoutHyphens.slice(8, 12)}-${uuidWithoutHyphens.slice(12, 16)}-${uuidWithoutHyphens.slice(16, 20)}-${uuidWithoutHyphens.slice(20)}`
}

/**
 * Removes hyphens from a UUID string.
 *
 * UUIDs are typically represented in the following format:
 * xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
 *
 * This function removes the hyphens, returning a continuous string of 32 characters.
 *
 * Example:
 * Input: "123e4567-e89b-12d3-a456-426655440000"
 * Output: "123e4567e89b12d3a456426655440000"
 *
 * @param uuidWithHyphens - The UUID string with hyphens.
 * @returns The UUID string without hyphens.
 * @throws Will throw an error if the input is not a valid UUID format (36 characters including hyphens).
 */
export function removeHyphensFromUUID(uuidWithHyphens: string): string {
  if (
    uuidWithHyphens.length !== 36 ||
    !/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(
      uuidWithHyphens
    )
  ) {
    throw new Error('Invalid UUID format. Expected a 36 character string with hyphens.')
  }

  return uuidWithHyphens.replace(/-/g, '')
}

export const useStartAppParams = () => {
  const launchParams = useLaunchParams()
  const startAppParams = launchParams.initData?.startParam
  if (!startAppParams) {
    return null
  }
  const startAppParam = startAppParams.startsWith('startapp=')
    ? (startAppParams.split('startapp=')[1] ?? '')
    : startAppParams

  if (startAppParam.startsWith('gen')) {
    const shortUUID = startAppParam.split('gen')[1]
    const uuid = restoreUUID(shortUUID)
    return { gen_art_id: uuid }
  }

  return startAppParam
}
