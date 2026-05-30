import type {
  Button,
  ConfigProvider,
  Radio,
  Select,
  Spin,
  Textarea,
} from "ant-design-vue";

declare module "@vue/runtime-core" {
  interface GlobalComponents {
    AButton: typeof Button;
    AConfigProvider: typeof ConfigProvider;
    ARadioGroup: typeof Radio.Group;
    ARadioButton: typeof Radio.Button;
    ASelect: typeof Select;
    ASpin: typeof Spin;
    ATextarea: typeof Textarea;
  }
}

export {};
