#!/usr/bin/env python3

from fastmcp import FastMCP
import aiohttp
import asyncio
import json
from typing import Dict, List, Optional, Any

# Initialize the MCP server with FastMCP framework
mcp = FastMCP(name="Akingbenga1 Viral Together MCP Server")

# Base URL for the API
BASE_URL = "https://github.com/Akingbenga1/viral-together"

async def make_request(method: str, url: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Helper function to make HTTP requests"""
    async with aiohttp.ClientSession() as session:
        if method.upper() == "GET":
            async with session.get(url, headers=headers) as response:
                return {
                    "status_code": response.status,
                    "data": await response.json() if response.content_type == 'application/json' else await response.text(),
                    "success": 200 <= response.status < 300
                }
        elif method.upper() == "POST":
            async with session.post(url, json=data, headers=headers) as response:
                return {
                    "status_code": response.status,
                    "data": await response.json() if response.content_type == 'application/json' else await response.text(),
                    "success": 200 <= response.status < 300
                }
        elif method.upper() == "PUT":
            async with session.put(url, json=data, headers=headers) as response:
                return {
                    "status_code": response.status,
                    "data": await response.json() if response.content_type == 'application/json' else await response.text(),
                    "success": 200 <= response.status < 300
                }
        elif method.upper() == "DELETE":
            async with session.delete(url, headers=headers) as response:
                return {
                    "status_code": response.status,
                    "data": await response.json() if response.content_type == 'application/json' else await response.text(),
                    "success": 200 <= response.status < 300
                }

@mcp.tool
def post_request(url: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Make a POST request to the viral-together API.
    
    Args:
        url: The full URL for the POST request
        data: Optional data to send in the request body
        headers: Optional headers for the request
    """
    return asyncio.run(make_request("POST", url, data, headers))

@mcp.tool
def get_request(url: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Make a GET request to the viral-together API.
    
    Args:
        url: The full URL for the GET request
        headers: Optional headers for the request
    """
    return asyncio.run(make_request("GET", url, None, headers))

@mcp.tool
def put_request(url: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Make a PUT request to the viral-together API.
    
    Args:
        url: The full URL for the PUT request
        data: Optional data to send in the request body
        headers: Optional headers for the request
    """
    return asyncio.run(make_request("PUT", url, data, headers))

@mcp.tool
def delete_request(url: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Make a DELETE request to the viral-together API.
    
    Args:
        url: The full URL for the DELETE request
        headers: Optional headers for the request
    """
    return asyncio.run(make_request("DELETE", url, None, headers))

# Agent Management Tools
@mcp.tool
def get_agent_by_id(agent_id: str) -> Dict[str, Any]:
    """Get agent information by ID."""
    url = f"{BASE_URL}/api/agents/{agent_id}"
    return get_request(url)

@mcp.tool
def get_all_agents() -> Dict[str, Any]:
    """Get all available agents."""
    url = f"{BASE_URL}/api/agents"
    return get_request(url)

# Response Management Tools
@mcp.tool
def create_response(user_id: str, task_id: str, content: str) -> Dict[str, Any]:
    """Create a new response for a task."""
    url = f"{BASE_URL}/api/responses"
    data = {"user_id": user_id, "task_id": task_id, "content": content}
    return post_request(url, data)

@mcp.tool
def get_user_responses(user_id: str) -> Dict[str, Any]:
    """Get all responses for a specific user."""
    url = f"{BASE_URL}/api/responses/user/{user_id}"
    return get_request(url)

@mcp.tool
def get_task_responses(task_id: str) -> Dict[str, Any]:
    """Get all responses for a specific task."""
    url = f"{BASE_URL}/api/responses/task/{task_id}"
    return get_request(url)

# Association Management Tools
@mcp.tool
def create_association(user_id: str, agent_id: str, is_primary: bool = False) -> Dict[str, Any]:
    """Create an association between a user and an agent."""
    url = f"{BASE_URL}/api/associations"
    data = {"user_id": user_id, "agent_id": agent_id, "is_primary": is_primary}
    return post_request(url, data)

@mcp.tool
def delete_association(user_id: str, agent_id: str) -> Dict[str, Any]:
    """Delete an association between a user and an agent."""
    url = f"{BASE_URL}/api/associations/{user_id}/{agent_id}"
    return delete_request(url)

@mcp.tool
def get_user_associations(user_id: str) -> Dict[str, Any]:
    """Get all agent associations for a user."""
    url = f"{BASE_URL}/api/associations/user/{user_id}"
    return get_request(url)

@mcp.tool
def get_agent_associations(agent_id: str) -> Dict[str, Any]:
    """Get all user associations for an agent."""
    url = f"{BASE_URL}/api/associations/agent/{agent_id}"
    return get_request(url)

@mcp.tool
def get_primary_associations(user_id: str) -> Dict[str, Any]:
    """Get primary associations for a user."""
    url = f"{BASE_URL}/api/associations/user/{user_id}/primary"
    return get_request(url)

# Coordination Session Tools
@mcp.tool
def create_coordination_session(user_id: str, agent_ids: List[str]) -> Dict[str, Any]:
    """Create a coordination session between multiple agents."""
    url = f"{BASE_URL}/api/coordination-sessions"
    data = {"user_id": user_id, "agent_ids": agent_ids}
    return post_request(url, data)

@mcp.tool
def assign_coordination_session(coordination_uuid: str, agent_id: str) -> Dict[str, Any]:
    """Assign an agent to a coordination session."""
    url = f"{BASE_URL}/api/coordination-sessions/{coordination_uuid}/assign"
    data = {"agent_id": agent_id}
    return post_request(url, data)

@mcp.tool
def get_coordination_agents(user_id: str) -> Dict[str, Any]:
    """Get coordination agents for a user."""
    url = f"{BASE_URL}/api/coordination/agents/{user_id}"
    return get_request(url)

@mcp.tool
def create_coordination_context(context_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create coordination context."""
    url = f"{BASE_URL}/api/coordination/context"
    return post_request(url, context_data)

# Conversation Management Tools
@mcp.tool
def create_conversation(user_id: str, title: str = None) -> Dict[str, Any]:
    """Create a new conversation."""
    url = f"{BASE_URL}/api/conversations"
    data = {"user_id": user_id, "title": title}
    return post_request(url, data)

@mcp.tool
def get_user_conversations(user_id: str) -> Dict[str, Any]:
    """Get all conversations for a user."""
    url = f"{BASE_URL}/api/conversations/{user_id}"
    return get_request(url)

@mcp.tool
def get_conversation_history(user_id: str) -> Dict[str, Any]:
    """Get conversation history for a user."""
    url = f"{BASE_URL}/api/conversations/{user_id}/history"
    return get_request(url)

# User Management Tools
@mcp.tool
def register_user(email: str, password: str, first_name: str, last_name: str) -> Dict[str, Any]:
    """Register a new user account."""
    url = f"{BASE_URL}/api/register"
    data = {"email": email, "password": password, "first_name": first_name, "last_name": last_name}
    return post_request(url, data)

@mcp.tool
def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    """Authenticate a user and get access token."""
    url = f"{BASE_URL}/api/token"
    data = {"email": email, "password": password}
    return post_request(url, data)

@mcp.tool
def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new user."""
    url = f"{BASE_URL}/api/user"
    return post_request(url, user_data)

@mcp.tool
def get_user_profile(user_id: str) -> Dict[str, Any]:
    """Get user profile information."""
    url = f"{BASE_URL}/api/profile/{user_id}"
    return get_request(url)

@mcp.tool
def get_user_data(user_id: str) -> Dict[str, Any]:
    """Get user data."""
    url = f"{BASE_URL}/api/data/{user_id}"
    return get_request(url)

@mcp.tool
def update_user_settings(user_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """Update user account settings."""
    url = f"{BASE_URL}/api/protected/update-settings"
    data = {"user_id": user_id, "settings": settings}
    return post_request(url, data)

@mcp.tool
def delete_user_account(user_id: str) -> Dict[str, Any]:
    """Delete user account."""
    url = f"{BASE_URL}/api/protected/delete-account"
    data = {"user_id": user_id}
    return delete_request(url, data)

# Messaging Tools
@mcp.tool
def send_message(user_id: str, agent_id: str, message: str) -> Dict[str, Any]:
    """Send a message to an agent."""
    url = f"{BASE_URL}/api/message"
    data = {"user_id": user_id, "agent_id": agent_id, "message": message}
    return post_request(url, data)

@mcp.tool
def send_public_message(message: str) -> Dict[str, Any]:
    """Send a public message."""
    url = f"{BASE_URL}/api/message/public"
    data = {"message": message}
    return post_request(url, data)

@mcp.tool
def create_suggestion(suggestion_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a suggestion."""
    url = f"{BASE_URL}/api/suggestions"
    return post_request(url, suggestion_data)

# Influencer Management Tools
@mcp.tool
def create_influencer_targets(target_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create influencer targets."""
    url = f"{BASE_URL}/api/influencers/targets/"
    return post_request(url, target_data)

@mcp.tool
def get_influencer_targets() -> Dict[str, Any]:
    """Get influencer targets."""
    url = f"{BASE_URL}/api/influencers/targets/"
    return get_request(url)

@mcp.tool
def generate_user_id(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate user ID."""
    url = f"{BASE_URL}/api/generate/{user_data.get('user_id', 'default')}"
    return post_request(url, user_data)

@mcp.tool
def analyze_custom_text(text_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze custom text."""
    url = f"{BASE_URL}/api/custom-text/analysis"
    return post_request(url, text_data)

# User and Recommendation Tools
@mcp.tool
def get_user_by_id(user_id: str) -> Dict[str, Any]:
    """Get user by ID."""
    url = f"{BASE_URL}/api/user/{user_id}"
    return get_request(url)

@mcp.tool
def get_recommendation_by_id(recommendation_id: str) -> Dict[str, Any]:
    """Get recommendation by ID."""
    url = f"{BASE_URL}/api/recommendation/{recommendation_id}"
    return get_request(url)

@mcp.tool
def update_recommendation(recommendation_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update recommendation."""
    url = f"{BASE_URL}/api/recommendation/{recommendation_id}"
    return put_request(url, data)

@mcp.tool
def delete_recommendation(recommendation_id: str) -> Dict[str, Any]:
    """Delete recommendation."""
    url = f"{BASE_URL}/api/recommendation/{recommendation_id}"
    return delete_request(url)

@mcp.tool
def trigger_analysis(user_id: str) -> Dict[str, Any]:
    """Trigger analysis for user."""
    url = f"{BASE_URL}/api/trigger-analysis/{user_id}"
    return post_request(url, {})

# Role Management Tools
@mcp.tool
def get_user_roles(user_id: str) -> Dict[str, Any]:
    """Get user roles."""
    url = f"{BASE_URL}/api/users/{user_id}/roles"
    return get_request(url)

@mcp.tool
def assign_role_to_user(user_id: str, role_id: str) -> Dict[str, Any]:
    """Assign role to user."""
    url = f"{BASE_URL}/api/users/{user_id}/roles/{role_id}"
    return post_request(url, {})

@mcp.tool
def remove_role_from_user(user_id: str, role_id: str) -> Dict[str, Any]:
    """Remove role from user."""
    url = f"{BASE_URL}/api/users/{user_id}/roles/{role_id}"
    return delete_request(url)

@mcp.tool
def get_all_roles() -> Dict[str, Any]:
    """Get all roles."""
    url = f"{BASE_URL}/api/roles"
    return get_request(url)

@mcp.tool
def get_all_users() -> Dict[str, Any]:
    """Get all users."""
    url = f"{BASE_URL}/api/users"
    return get_request(url)

# Blog Management Tools
@mcp.tool
def create_blog(blog_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a blog post."""
    url = f"{BASE_URL}/api/blogs/create"
    return post_request(url, blog_data)

@mcp.tool
def update_blog(blog_id: str, blog_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a blog post."""
    url = f"{BASE_URL}/api/blogs/update/{blog_id}"
    return put_request(url, blog_data)

@mcp.tool
def get_all_blogs() -> Dict[str, Any]:
    """Get all blogs."""
    url = f"{BASE_URL}/api/blogs"
    return get_request(url)

@mcp.tool
def get_blog_by_slug(slug: str) -> Dict[str, Any]:
    """Get blog by slug."""
    url = f"{BASE_URL}/api/blogs/{slug}"
    return get_request(url)

@mcp.tool
def get_admin_blogs() -> Dict[str, Any]:
    """Get admin blogs."""
    url = f"{BASE_URL}/api/admin/blogs"
    return get_request(url)

@mcp.tool
def delete_blog(blog_id: str) -> Dict[str, Any]:
    """Delete a blog post."""
    url = f"{BASE_URL}/api/delete/blog/{blog_id}"
    return delete_request(url)

@mcp.tool
def upload_image(image_data: Dict[str, Any]) -> Dict[str, Any]:
    """Upload an image."""
    url = f"{BASE_URL}/api/upload/image"
    return post_request(url, image_data)

@mcp.tool
def create_public_blog(blog_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a public blog post."""
    url = f"{BASE_URL}/api/blogs/create/public"
    return post_request(url, blog_data)

# Business Management Tools
@mcp.tool
def create_business(business_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a business."""
    url = f"{BASE_URL}/api/businesses/create"
    return post_request(url, business_data)

@mcp.tool
def get_business_by_id(business_id: str) -> Dict[str, Any]:
    """Get business by ID."""
    url = f"{BASE_URL}/api/businesses/get_business_by_id/{business_id}"
    return get_request(url)

@mcp.tool
def update_business(business_id: str, business_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a business."""
    url = f"{BASE_URL}/api/businesses/{business_id}"
    return put_request(url, business_data)

@mcp.tool
def delete_business(business_id: str) -> Dict[str, Any]:
    """Delete a business."""
    url = f"{BASE_URL}/api/businesses/{business_id}"
    return delete_request(url)

@mcp.tool
def get_all_businesses() -> Dict[str, Any]:
    """Get all businesses."""
    url = f"{BASE_URL}/api/businesses/get_all"
    return get_request(url)

# Collaboration Tools
@mcp.tool
def search_businesses_by_base_country(country: str) -> Dict[str, Any]:
    """Search businesses by base country."""
    url = f"{BASE_URL}/api/businesses/search_by_base_country"
    data = {"country": country}
    return post_request(url, data)

@mcp.tool
def search_businesses_by_collaboration_country(country: str) -> Dict[str, Any]:
    """Search businesses by collaboration country."""
    url = f"{BASE_URL}/api/businesses/search_by_collaboration_country"
    data = {"country": country}
    return post_request(url, data)

@mcp.tool
def get_collaboration_by_id(collaboration_id: str) -> Dict[str, Any]:
    """Get collaboration by ID."""
    url = f"{BASE_URL}/api/collaborations/{collaboration_id}"
    return get_request(url)

@mcp.tool
def update_collaboration(collaboration_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update collaboration."""
    url = f"{BASE_URL}/api/collaborations/{collaboration_id}"
    return put_request(url, data)

@mcp.tool
def delete_collaboration(collaboration_id: str) -> Dict[str, Any]:
    """Delete collaboration."""
    url = f"{BASE_URL}/api/collaborations/{collaboration_id}"
    return delete_request(url)

@mcp.tool
def approve_collaboration(collaboration_id: str) -> Dict[str, Any]:
    """Approve collaboration."""
    url = f"{BASE_URL}/api/collaborations/{collaboration_id}/approve"
    return post_request(url, {})

@mcp.tool
def approve_multiple_collaborations(collaboration_ids: List[str]) -> Dict[str, Any]:
    """Approve multiple collaborations."""
    url = f"{BASE_URL}/api/collaborations/approve_multiple"
    data = {"collaboration_ids": collaboration_ids}
    return post_request(url, data)

# Country and Region Tools
@mcp.tool
def get_all_countries() -> Dict[str, Any]:
    """Get all countries."""
    url = f"{BASE_URL}/api/countries"
    return get_request(url)

@mcp.tool
def get_regions() -> Dict[str, Any]:
    """Get all regions."""
    url = f"{BASE_URL}/api/regions"
    return get_request(url)

@mcp.tool
def get_country_by_id(country_id: str) -> Dict[str, Any]:
    """Get country by ID."""
    url = f"{BASE_URL}/api/countries/{country_id}"
    return get_request(url)

# AI Generation Tools
@mcp.tool
def generate_content(generation_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate content using AI."""
    url = f"{BASE_URL}/api/generate"
    return post_request(url, generation_data)

@mcp.tool
def generate_business_plan(business_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate business plan using AI."""
    url = f"{BASE_URL}/api/generate/business-plan"
    return post_request(url, business_data)

@mcp.tool
def generate_collaboration_request_specific(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate specific collaboration request."""
    url = f"{BASE_URL}/api/generate/collaboration-request/specific"
    return post_request(url, request_data)

@mcp.tool
def generate_collaboration_request_general(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate general collaboration request."""
    url = f"{BASE_URL}/api/generate/collaboration-request/general"
    return post_request(url, request_data)

@mcp.tool
def generate_collaboration_request_public(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate public collaboration request."""
    url = f"{BASE_URL}/api/generate/collaboration-request/public"
    return post_request(url, request_data)

@mcp.tool
def generate_market_analysis_public(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate public market analysis."""
    url = f"{BASE_URL}/api/generate/market-analysis/public"
    return post_request(url, analysis_data)

@mcp.tool
def generate_social_media_plan_public(plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate public social media plan."""
    url = f"{BASE_URL}/api/generate/social-media-plan/public"
    return post_request(url, plan_data)

@mcp.tool
def generate_business_plan_public(plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate public business plan."""
    url = f"{BASE_URL}/api/generate/business-plan/public"
    return post_request(url, plan_data)

# Document Management Tools
@mcp.tool
def get_document_status(document_id: str) -> Dict[str, Any]:
    """Get document status."""
    url = f"{BASE_URL}/api/documents/{document_id}/status"
    return get_request(url)

@mcp.tool
def download_document(document_id: str) -> Dict[str, Any]:
    """Download document."""
    url = f"{BASE_URL}/api/documents/{document_id}/download"
    return get_request(url)

@mcp.tool
def upload_document(document_data: Dict[str, Any]) -> Dict[str, Any]:
    """Upload document."""
    url = f"{BASE_URL}/api/documents/upload"
    return post_request(url, document_data)

@mcp.tool
def auto_source_document(document_data: Dict[str, Any]) -> Dict[str, Any]:
    """Auto source document."""
    url = f"{BASE_URL}/api/documents/auto-source"
    return post_request(url, document_data)

# Template Management Tools
@mcp.tool
def get_all_templates() -> Dict[str, Any]:
    """Get all templates."""
    url = f"{BASE_URL}/api/templates"
    return get_request(url)

@mcp.tool
def get_template_by_id(template_id: str) -> Dict[str, Any]:
    """Get template by ID."""
    url = f"{BASE_URL}/api/templates/{template_id}"
    return get_request(url)

@mcp.tool
def delete_template(template_id: str) -> Dict[str, Any]:
    """Delete template."""
    url = f"{BASE_URL}/api/templates/{template_id}"
    return delete_request(url)

# Influencer Management Tools
@mcp.tool
def create_influencer(influencer_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create influencer."""
    url = f"{BASE_URL}/api/influencers/create"
    return post_request(url, influencer_data)

@mcp.tool
def create_public_influencer(influencer_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create public influencer."""
    url = f"{BASE_URL}/api/influencers/create/public"
    return post_request(url, influencer_data)

@mcp.tool
def get_influencer_by_id(influencer_id: str) -> Dict[str, Any]:
    """Get influencer by ID."""
    url = f"{BASE_URL}/api/influencers/get_influencer/{influencer_id}"
    return get_request(url)

@mcp.tool
def update_influencer(influencer_id: str, influencer_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update influencer."""
    url = f"{BASE_URL}/api/influencers/update_influencer/{influencer_id}"
    return put_request(url, influencer_data)

@mcp.tool
def delete_influencer(influencer_id: str) -> Dict[str, Any]:
    """Delete influencer."""
    url = f"{BASE_URL}/api/influencers/remove_influencer/{influencer_id}"
    return delete_request(url)

@mcp.tool
def list_influencers() -> Dict[str, Any]:
    """List all influencers."""
    url = f"{BASE_URL}/api/influencers/list"
    return get_request(url)

@mcp.tool
def search_influencers_by_base_country(country: str) -> Dict[str, Any]:
    """Search influencers by base country."""
    url = f"{BASE_URL}/api/influencers/search_by_base_country"
    data = {"country": country}
    return post_request(url, data)

@mcp.tool
def search_influencers_by_collaboration_country(country: str) -> Dict[str, Any]:
    """Search influencers by collaboration country."""
    url = f"{BASE_URL}/api/influencers/search_by_collaboration_country"
    data = {"country": country}
    return post_request(url, data)

@mcp.tool
def search_influencers_by_criteria(criteria: Dict[str, Any]) -> Dict[str, Any]:
    """Search influencers by criteria."""
    url = f"{BASE_URL}/api/influencers/search_by_criteria"
    return post_request(url, criteria)

# Notification Management Tools
@mcp.tool
def get_notification_by_id(notification_id: str) -> Dict[str, Any]:
    """Get notification by ID."""
    url = f"{BASE_URL}/api/notifications/{notification_id}"
    return get_request(url)

@mcp.tool
def mark_notification_read(notification_id: str) -> Dict[str, Any]:
    """Mark notification as read."""
    url = f"{BASE_URL}/api/notifications/{notification_id}/mark_read"
    return put_request(url, {})

@mcp.tool
def delete_notification(notification_id: str) -> Dict[str, Any]:
    """Delete notification."""
    url = f"{BASE_URL}/api/notifications/{notification_id}"
    return delete_request(url)

@mcp.tool
def get_notification_stats() -> Dict[str, Any]:
    """Get notification statistics."""
    url = f"{BASE_URL}/api/notifications/stats"
    return get_request(url)

@mcp.tool
def get_unread_notification_count() -> Dict[str, Any]:
    """Get unread notification count."""
    url = f"{BASE_URL}/api/notifications/unread_count"
    return get_request(url)

@mcp.tool
def mark_all_notifications_read() -> Dict[str, Any]:
    """Mark all notifications as read."""
    url = f"{BASE_URL}/api/notifications/mark_all_read"
    return put_request(url, {})

@mcp.tool
def bulk_mark_notifications_read(notification_ids: List[str]) -> Dict[str, Any]:
    """Bulk mark notifications as read."""
    url = f"{BASE_URL}/api/notifications/bulk_mark_read"
    data = {"notification_ids": notification_ids}
    return put_request(url, data)

@mcp.tool
def bulk_delete_notifications(notification_ids: List[str]) -> Dict[str, Any]:
    """Bulk delete notifications."""
    url = f"{BASE_URL}/api/notifications/bulk_delete"
    data = {"notification_ids": notification_ids}
    return delete_request(url, data)

# Preference Management Tools
@mcp.tool
def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """Get user preferences."""
    url = f"{BASE_URL}/api/preferences/{user_id}"
    return get_request(url)

@mcp.tool
def create_user_preference(user_id: str, event_type: str, preference_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create user preference."""
    url = f"{BASE_URL}/api/preferences/{user_id}/{event_type}"
    return post_request(url, preference_data)

@mcp.tool
def update_user_preference(user_id: str, event_type: str, preference_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update user preference."""
    url = f"{BASE_URL}/api/preferences/{user_id}/{event_type}"
    return put_request(url, preference_data)

@mcp.tool
def delete_user_preference(user_id: str, event_type: str) -> Dict[str, Any]:
    """Delete user preference."""
    url = f"{BASE_URL}/api/preferences/{user_id}/{event_type}"
    return delete_request(url)

# Admin Tools
@mcp.tool
def get_admin_stats() -> Dict[str, Any]:
    """Get admin statistics."""
    url = f"{BASE_URL}/api/admin/stats"
    return get_request(url)

# Promotion Management Tools
@mcp.tool
def get_promotion_by_id(promotion_id: str) -> Dict[str, Any]:
    """Get promotion by ID."""
    url = f"{BASE_URL}/api/promotions/{promotion_id}"
    return get_request(url)

@mcp.tool
def update_promotion(promotion_id: str, promotion_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update promotion."""
    url = f"{BASE_URL}/api/promotions/{promotion_id}"
    return put_request(url, promotion_data)

@mcp.tool
def delete_promotion(promotion_id: str) -> Dict[str, Any]:
    """Delete promotion."""
    url = f"{BASE_URL}/api/promotions/{promotion_id}"
    return delete_request(url)

@mcp.tool
def show_interest_in_promotion(promotion_id: str, interest_data: Dict[str, Any]) -> Dict[str, Any]:
    """Show interest in promotion."""
    url = f"{BASE_URL}/api/promotions/{promotion_id}/show_interest"
    return post_request(url, interest_data)

# Rate Card Management Tools
@mcp.tool
def create_rate_card(rate_card_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create rate card."""
    url = f"{BASE_URL}/api/rate-cards/create"
    return post_request(url, rate_card_data)

@mcp.tool
def get_rate_card_by_id(rate_card_id: str) -> Dict[str, Any]:
    """Get rate card by ID."""
    url = f"{BASE_URL}/api/rate-cards/get_rate_card/{rate_card_id}"
    return get_request(url)

@mcp.tool
def get_influencer_rate_cards(influencer_id: str) -> Dict[str, Any]:
    """Get influencer rate cards."""
    url = f"{BASE_URL}/api/rate-cards/influencer/{influencer_id}"
    return get_request(url)

@mcp.tool
def update_rate_card(rate_card_id: str, rate_card_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update rate card."""
    url = f"{BASE_URL}/api/rate-cards/update_rate_card/{rate_card_id}"
    return put_request(url, rate_card_data)

@mcp.tool
def delete_rate_card(rate_card_id: str) -> Dict[str, Any]:
    """Delete rate card."""
    url = f"{BASE_URL}/api/rate-cards/delete_rate_card/{rate_card_id}"
    return delete_request(url)

@mcp.tool
def get_influencer_rate_summary(influencer_id: str) -> Dict[str, Any]:
    """Get influencer rate summary."""
    url = f"{BASE_URL}/api/rate-cards/influencer/{influencer_id}/rate_summary"
    return get_request(url)

@mcp.tool
def search_rate_cards(min_rate: float, max_rate: float) -> Dict[str, Any]:
    """Search rate cards by price range."""
    url = f"{BASE_URL}/api/rate-cards/search/{min_rate}/{max_rate}"
    return get_request(url)

@mcp.tool
def get_platform_rate_cards(platform_id: str) -> Dict[str, Any]:
    """Get platform rate cards."""
    url = f"{BASE_URL}/api/rate-cards/platform/{platform_id}"
    return get_request(url)

# Rate Proposal Management Tools
@mcp.tool
def create_rate_proposal(proposal_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create rate proposal."""
    url = f"{BASE_URL}/api/rate-proposals/create"
    return post_request(url, proposal_data)

@mcp.tool
def get_rate_proposal_by_id(proposal_id: str) -> Dict[str, Any]:
    """Get rate proposal by ID."""
    url = f"{BASE_URL}/api/rate-proposals/{proposal_id}"
    return get_request(url)

@mcp.tool
def update_rate_proposal(proposal_id: str, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update rate proposal."""
    url = f"{BASE_URL}/api/rate-proposals/{proposal_id}"
    return put_request(url, proposal_data)

@mcp.tool
def delete_rate_proposal(proposal_id: str) -> Dict[str, Any]:
    """Delete rate proposal."""
    url = f"{BASE_URL}/api/rate-proposals/{proposal_id}"
    return delete_request(url)

@mcp.tool
def get_influencer_rate_proposals(influencer_id: str) -> Dict[str, Any]:
    """Get influencer rate proposals."""
    url = f"{BASE_URL}/api/rate-proposals/influencer/{influencer_id}"
    return get_request(url)

@mcp.tool
def get_business_rate_proposals(business_id: str) -> Dict[str, Any]:
    """Get business rate proposals."""
    url = f"{BASE_URL}/api/rate-proposals/business/{business_id}"
    return get_request(url)

# Platform Management Tools
@mcp.tool
def create_platform(platform_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create platform."""
    url = f"{BASE_URL}/api/platforms/create"
    return post_request(url, platform_data)

@mcp.tool
def list_platforms() -> Dict[str, Any]:
    """List all platforms."""
    url = f"{BASE_URL}/api/platforms/list"
    return get_request(url)

@mcp.tool
def get_platform_by_id(platform_id: str) -> Dict[str, Any]:
    """Get platform by ID."""
    url = f"{BASE_URL}/api/platforms/{platform_id}"
    return get_request(url)

@mcp.tool
def update_platform(platform_id: str, platform_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update platform."""
    url = f"{BASE_URL}/api/platforms/{platform_id}"
    return put_request(url, platform_data)

@mcp.tool
def delete_platform(platform_id: str) -> Dict[str, Any]:
    """Delete platform."""
    url = f"{BASE_URL}/api/platforms/{platform_id}"
    return delete_request(url)

# Subscription Management Tools
@mcp.tool
def create_subscription_plan(plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create subscription plan."""
    url = f"{BASE_URL}/api/subscriptions/plans"
    return post_request(url, plan_data)

@mcp.tool
def get_all_subscription_plans() -> Dict[str, Any]:
    """Get all subscription plans."""
    url = f"{BASE_URL}/api/subscriptions/plans"
    return get_request(url)

@mcp.tool
def get_subscription_plan_by_id(plan_id: str) -> Dict[str, Any]:
    """Get subscription plan by ID."""
    url = f"{BASE_URL}/api/subscriptions/plans/{plan_id}"
    return get_request(url)

@mcp.tool
def update_subscription_plan(plan_id: str, plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update subscription plan."""
    url = f"{BASE_URL}/api/subscriptions/plans/{plan_id}"
    return put_request(url, plan_data)

@mcp.tool
def create_checkout_session(checkout_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create checkout session."""
    url = f"{BASE_URL}/api/subscriptions/checkout"
    return post_request(url, checkout_data)

@mcp.tool
def create_customer_portal(portal_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create customer portal."""
    url = f"{BASE_URL}/api/subscriptions/portal"
    return post_request(url, portal_data)

@mcp.tool
def get_my_subscription() -> Dict[str, Any]:
    """Get my subscription."""
    url = f"{BASE_URL}/api/subscriptions/my_subscription"
    return get_request(url)

@mcp.tool
def handle_webhook(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle webhook."""
    url = f"{BASE_URL}/api/subscriptions/webhook"
    return post_request(url, webhook_data)

@mcp.tool
def get_all_subscriptions() -> Dict[str, Any]:
    """Get all subscriptions."""
    url = f"{BASE_URL}/api/subscriptions"
    return get_request(url)

@mcp.tool
def get_user_subscriptions(user_id: str) -> Dict[str, Any]:
    """Get user subscriptions."""
    url = f"{BASE_URL}/api/subscriptions/users/{user_id}"
    return get_request(url)

@mcp.tool
def get_api_documentation() -> Dict[str, Any]:
    """Get API documentation."""
    url = f"{BASE_URL}/api"
    return get_request(url)

if __name__ == "__main__":
    print(f"""
{'='*60}
Akingbenga1 Viral Together MCP Server
Using FastMCP Framework Style
{'='*60}

Available Tools (145 endpoints):
- HTTP Methods: post_request, get_request, put_request, delete_request
- Agent Management: get_agent_by_id, get_all_agents
- Response Management: create_response, get_user_responses, get_task_responses
- Association Management: create_association, delete_association, get_user_associations
- Coordination: create_coordination_session, assign_coordination_session
- Conversations: create_conversation, get_user_conversations, get_conversation_history
- User Management: register_user, authenticate_user, get_user_profile, update_user_settings
- Messaging: send_message, send_public_message, create_suggestion
- Influencer Management: create_influencer, get_influencer_by_id, update_influencer
- Business Management: create_business, get_business_by_id, update_business
- Collaboration: search_businesses_by_base_country, approve_collaboration
- AI Generation: generate_business_plan, generate_market_analysis, generate_social_media_plan
- Document Management: upload_document, get_document_status, download_document
- Template Management: get_all_templates, get_template_by_id, delete_template
- Notification Management: get_notification_by_id, mark_notification_read
- Preference Management: get_user_preferences, create_user_preference
- Promotion Management: get_promotion_by_id, show_interest_in_promotion
- Rate Card Management: create_rate_card, get_rate_card_by_id, update_rate_card
- Rate Proposal Management: create_rate_proposal, get_rate_proposal_by_id
- Platform Management: create_platform, list_platforms, get_platform_by_id
- Subscription Management: create_subscription_plan, get_all_subscription_plans
- And many more...

Starting server with HTTP transport...
{'='*60}
""")
    
    # Run the server with HTTP transport (like standard_mcp_server.py)
    mcp.run(transport="http", port=8000)
