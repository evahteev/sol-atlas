"""
Process handlers package.
"""
from aiogram import Router

from . import start_process
from . import start_form_handlers
from . import unified_form_handlers
from . import task_actions
from . import file_upload
from . import dialog_form
from . import process_settings_handlers

# Create main processes router
router = Router(name="processes")

# Include sub-routers (ORDER MATTERS!)
# Note: Form input routing is handled by FormInputMiddleware (registered in __main__.py)
# The middleware checks FSM state and routes to form handlers when needed.
# These routers contain STATE-BASED handlers that match specific FSM states.
router.include_router(start_process.router)
router.include_router(unified_form_handlers.router)  # Unified form handling (start forms + tasks)
router.include_router(dialog_form.router)  # State-based form handlers (ProcessStates.waiting_for_input)
router.include_router(start_form_handlers.router)  # State-dependent handlers (requires ProcessStates.waiting_for_input)
router.include_router(task_actions.router)
router.include_router(file_upload.router)
router.include_router(process_settings_handlers.router)  # Process instance management

__all__ = ["router"]

