"""FastAPI routes: POST /optimize, GET /sessions, GET /sessions/{id}."""

# TODO: Implement POST /optimize endpoint
#   - Request body: OptimizationRequest DTO
#   - Extract tenant_id from JWT token (via middleware)
#   - Call OptimizationApplicationService.run_optimization()
#   - Return OptimizationResponse DTO
#   - Error handling: 400 for validation errors, 500 for server errors
# TODO: Implement GET /sessions endpoint
#   - Query params: page, page_size (optional)
#   - Extract tenant_id from JWT token
#   - Return paginated list of SessionDetailDTO
# TODO: Implement GET /sessions/{id} endpoint
#   - Path param: session_id (UUID)
#   - Extract tenant_id from JWT token
#   - Return SessionDetailDTO
#   - Error handling: 404 if session not found or belongs to different tenant
