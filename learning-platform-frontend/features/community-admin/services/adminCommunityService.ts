import {
  createCommunity,
  deleteCommunity,
  getCommunities,
  getDiscussionThreads,
  resolveDiscussionThread,
} from "@/services/communityService";
import { getTopics } from "@/services/topicService";

export async function getAdminCommunityBootstrap() {
  const [topics, communities] = await Promise.all([
    getTopics(),
    getCommunities({ limit: 50, offset: 0 }),
  ]);

  return {
    topics: topics.items,
    communities: communities.items,
  };
}

export async function getAdminCommunityThreads(communityId?: number) {
  return getDiscussionThreads({
    limit: 20,
    offset: 0,
    community_id: communityId,
  });
}

export {
  createCommunity as createAdminCommunity,
  deleteCommunity as deleteAdminCommunity,
  resolveDiscussionThread as resolveAdminDiscussionThread,
};
