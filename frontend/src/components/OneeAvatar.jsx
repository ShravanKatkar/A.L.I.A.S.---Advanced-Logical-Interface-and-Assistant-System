import React from 'react'
import { Avatar } from '@bible-strong/avatar-react'
import avatarDef from '../assets/onee-avatar-definition.json'

/**
 * OneeAvatar Component
 * Uses the official @bible-strong/avatar-react renderer for the Onee avatar definition.
 */
export default function OneeAvatar({
  animation = 'idle',
  expression = null,
  size = 180,
  className = '',
  onClick = null,
  style = {}
}) {
  return (
    <div
      onClick={onClick}
      className={`inline-flex items-center justify-center select-none transition-transform duration-200 ${onClick ? 'cursor-pointer hover:scale-105' : ''} ${className}`}
      style={style}
    >
      <Avatar
        definition={avatarDef}
        animation={expression ? undefined : (animation || 'idle')}
        expression={expression || undefined}
        size={size}
      />
    </div>
  )
}
