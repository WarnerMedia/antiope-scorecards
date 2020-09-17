const styles =
  {
    root: {
        display: 'flex',
        flexGrow: 1,

      },
      spreadsheetLink: {
        marginLeft: '2rem',
        color: 'black'
      },
      denied: {
        display: 'flex',
        flexGrow: 1,
        height: '100%',

      },
      content: {
        flexGrow: 1,
        height: "90%",
        paddingTop: "70px"
      },
      loadingContent: {
        flexGrow: 1,
        textAlign: "center",
        height: "90%",
        paddingTop: "70px"
      },
      exclusionsContent: {
        flexGrow: 1,
        height: "90%",
      },
      ncrContent: {
        flexGrow: 1,
        height: "100%",
      },
      search: {
        position: 'relative',
        borderRadius: 5,
        backgroundColor: '#eeeeee',
        '&:hover': {
          backgroundColor: '#e0e0e0',
        },
        marginRight: 5,
        marginLeft: '0',
        width: '400px',
        height: '40px',
      },
      searchIcon: {
        width: 20,
        height: '100%',
        position: 'absolute',
        pointerEvents: 'none',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        paddingLeft: '10px'
      },
      inputRoot: {
        color: 'inherit',
        height: 'inherit'
      },
      inputInput: {
          paddingTop: '10px',
          transition: 5,
          width: '75px',
      },
      tool: {
          alignSelf: 'flex-end',
          display: 'flex',
          position: 'relative',
      },
      icon: {
          minWidth: "30px"
      },
      logo: {
          width: '180px',
          height: 'auto'
      },
      spacer: {
          flexGrow: 1
      },
      formControl: {
        marginLeft: '5px',
        minWidth: "300px",
        maxWidth: "300px",
      },
      chips: {
        display: 'flex',
        flexWrap: 'wrap',
      },
      chip: {
        margin: 2,
      },
      noLabel: {
        marginTop: '3 rem',
      },
      filterBar: {
        padding: '5px',
        marginBottom: '10px'
      },
      wrapper: {
        position: 'relative'
      },
      buttonProgress: {
        color: '#eeeee',
        position: 'absolute',
        top: '50%',
        left: '50%',
        marginTop: -12,
        marginLeft: -12,
      },
      loginProgress: {
        color: '#eeeee',
        position: 'absolute',
        top: '48%',
        left: '47%',
        marginTop: -12,
        marginLeft: -12,
      },
      tabs: {
        height: '63px',
        marginLeft: '3rem'
      },
      tab: {
        marginTop: '10px'
      },
      tableButton: {
        height: '25px',
        fontSize: '0.25rem',
        lineHeight: '0.5'
      },
      tableButtonLargeFont: {
        height: '25px',
        fontSize: '0.7rem',
        lineHeight: '0.5'
      },
      scanView: {
        'overflow-y': 'scroll',
        height: '100%'
      },
      fab: {
        right: '16px',
        bottom: '16px',
        position: 'absolute',
      },
      modalError: {
        color: '#f44336'
      }

  }

export default styles;
