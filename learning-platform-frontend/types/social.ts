export type SocialProfile = {
  user_id: number;
  display_name: string;
  email: string;
  role: string;
  xp: number;
  streak_days: number;
  completion_percent: number;
  top_skills: string[];
  weak_topics: string[];
  badges: string[];
  communities: string[];
  is_following: boolean;
  follower_count: number;
  following_count: number;
  tagline: string;
};

export type SocialFeedItem = {
  actor_user_id: number;
  actor_name: string;
  event_type: string;
  title: string;
  description: string;
  created_at: string;
  tone: string;
};

export type SocialPeerGroup = {
  title: string;
  description: string;
  members: SocialProfile[];
};

export type SocialNetworkResponse = {
  me: SocialProfile;
  following: SocialProfile[];
  suggested_people: SocialProfile[];
  feed: SocialFeedItem[];
  peer_groups: SocialPeerGroup[];
};
