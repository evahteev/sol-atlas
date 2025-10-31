export type TaskFormDeployedForm = {
  components: TaskFormDeployedComponent[]
  type: string
  id: string
}

export type TaskFormDeployedComponent = {
  label?: string | null
  description?: string | null
  layout: {
    row: string
    columns?: number | null
  }
  id: string
  key?: string | null
  properties?: Record<string, string> | null
} & (
  | { type: 'text'; text?: string }
  | { type: 'html'; content?: string }
  | { type: 'iframe'; url: string; security: Record<string, string>; height: number }
  | {
      type: 'select'
      defaultValue?: string | null
      values?: { label: string; value?: string }[]
      validate?: {
        required?: boolean
      }
      readonly?: string
      disabled?: boolean
    }
  | {
      type: 'checklist' | 'radio'
      defaultValue?: string | null
      values?: { label: string; value?: string }[]
      validate?: {
        required?: boolean
      }
      readonly?: string
      disabled?: boolean
    }
  | {
      type: 'filepicker'
      validate?: {
        required?: boolean
      }
      multiple?: string
      accept: string
      readonly?: string
      disabled?: boolean
    }
  | {
      type: 'number'
      validate?: {
        required?: boolean
        min?: number
        max?: number
      }
      defaultValue?: string | null
      appearance: { prefixAdorner: string; suffixAdorner: string }
      readonly?: string
      disabled?: boolean
    }
  | { type: 'image'; source?: string }
  | {
      type: 'textfield'
      defaultValue?: string
      validate?: {
        required?: boolean
        minLength?: number
        maxLength?: number
        pattern?: string
        validationType?: string
      }
      appearance: { prefixAdorner: string; suffixAdorner: string }
      readonly?: string
      disabled?: boolean
    }
  | {
      type: 'textarea'
      defaultValue?: string
      validate?: {
        required?: boolean
        minLength?: number
        maxLength?: number
        pattern?: string
      }
      readonly?: string
      disabled?: boolean
    }
  | {
      type: 'datetime'
      defaultValue?: string | null
      subtype?: 'date'
      dateLabel?: string
      validate?: {
        required?: boolean
      }
      readonly?: string
      disabled?: boolean
    }
  | { type: 'separator'; text?: string }
  | { type: 'group'; components?: TaskFormDeployedComponent[]; showOutline?: boolean }
  | {
      type: 'checkbox'
      validate?: {
        required?: boolean
      }
      readonly?: string
      disabled?: boolean
      defaultValue?: boolean
    }
  | { type: 'spacer' }
  | { type: 'button'; action: 'reset' | 'submit'; disabled?: boolean }
)
