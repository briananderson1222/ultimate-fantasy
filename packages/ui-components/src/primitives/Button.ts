export const Button = (props: any) => {
  return {
    props,
    designTokens: {
      colors: {},
      spacing: {},
    },
    styling: {
      type: props.platform === 'mobile' ? 'stylesheet' : 'tailwind',
    },
    theme: props.theme,
    themeTokens: {
      light: {
        primary: '',
      },
      dark: {
        primary: '',
      },
    },
  };
};

Button.propTypes = {};
Button.defaultProps = {};