import { mount } from '@vue/test-utils';

import Card from '@/components/layout/Card.vue';

function createWrapper(options?: { slot?: string }) {
  return mount(Card, {
    shallow: true,
    slots: {
      default: options?.slot ?? '',
    },
  });
}

describe('Card.vue', () => {
  it('renders given default slot', () => {
    const wrapper = createWrapper({ slot: '<span>test</span>' });

    expect(wrapper.html()).toContain('<span>test</span>');
  });

  it('has round corders', () => {
    const wrapper = createWrapper();

    expect(wrapper.classes()).toContain('rounded-lg');
  });

  it('has a shadow', () => {
    const wrapper = createWrapper();

    expect(wrapper.classes()).toContain('shadow');
  });
});
