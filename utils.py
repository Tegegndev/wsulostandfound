user_states = {}
pending_posts = {}


def get_user_state(chat_id: int):
	return user_states.get(chat_id)


def set_user_state(chat_id: int, state: dict):
	user_states[chat_id] = state


def clear_user_state(chat_id: int):
	user_states.pop(chat_id, None)


def has_user_state(chat_id: int) -> bool:
	return chat_id in user_states


def build_pending_id(chat_id: int) -> str:
	return f"{chat_id}_{len(pending_posts) + 1}"


def set_pending_post(pending_id: str, payload: dict):
	pending_posts[pending_id] = payload


def get_pending_post(pending_id: str):
	return pending_posts.get(pending_id)


def remove_pending_post(pending_id: str):
	pending_posts.pop(pending_id, None)

