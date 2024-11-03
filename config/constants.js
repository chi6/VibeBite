export const AGENT_TYPES = {
  "1": {
    name: "通用助手",
    description: "可以回答各种问题的AI助手"
  },
  "2": {
    name: "分析专家",
    description: "专注于分析问题和提供见解"
  },
  "3": {
    name: "领域专家",
    description: "专注于餐饮推荐和美食建议"
  }
};

export const DEFAULT_MESSAGES = {
  WELCOME: "你好！我是你的AI助手。我可以帮你推荐餐厅，你想吃什么类型的食物？",
  ERROR: "抱歉，我现在遇到了一些问题。请稍后再试。",
  SWITCH_AGENT: (agentType) => `已切换至${agentType}，有什么我可以帮你的吗？`
}; 